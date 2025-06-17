# routers/search.py

from fastapi import APIRouter, HTTPException
from typing import List
from app.models.product import Product, ProductDetailsResponse, ProductWithStatus, ProductMetadata, ProductActions, SearchRequest, SearchResponse
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_skus, get_all_products
from app.utils.logger import logger, log_with_context
from app.utils.redis_client import redis_client
from datetime import datetime

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
def search_products(payload: SearchRequest):
    """
    Search for products in the database with comprehensive Redis caching.

    Args:
        payload (SearchRequest): The search request containing the user's query.

    Returns:
        SearchResponse: A list of matching products.
    """
    query = payload.query.strip()
    top_k = getattr(payload, 'limit', 5)  # Default to 5 results
    
    # 1. Check if complete search result is cached
    if redis_client.is_connected():
        cached_results = redis_client.get_search_results(query, top_k)
        if cached_results:
            log_with_context(
                logger,
                "info",
                "Search results served from cache",
                query=query,
                limit=top_k,
                results_count=len(cached_results)
            )
            return {"results": [Product(**p) for p in cached_results]}
    
    log_with_context(
        logger,
        "info",
        "Processing search query",
        query=query,
        limit=top_k
    )
    
    # 2. Generate an embedding from the user's search query (with embedding cache)
    embedding = get_embedding(query)
    
    # 3. Use the embedding to find the SKUs of the most similar products in Qdrant (with vector cache)
    skus = search_in_qdrant(embedding, top_k=top_k)
    
    # 4. Retrieve the full product details from PostgreSQL using the SKUs found
    products = get_products_by_skus(skus)
    
    # 5. Cache the complete search results
    if redis_client.is_connected() and products:
        redis_client.set_search_results(query, products, top_k)
        log_with_context(
            logger,
            "info",
            "Search results cached",
            query=query,
            results_count=len(products)
        )
    
    log_with_context(
        logger,
        "info",
        "Search completed successfully",
        query=query,
        results_found=len(products),
        skus_found=len(skus)
    )
    
    # 6. Return the products found
    return {"results": [Product(**p) for p in products]}

@router.get("/products/{sku}", response_model=Product)
def get_product_by_sku(sku: str):
    """
    Get product details by SKU.
    
    Args:
        sku (str): The SKU of the product to retrieve
    
    Returns:
        Product: The product details
    """
    log_with_context(
        logger,
        "info",
        "Getting product details by SKU",
        sku=sku
    )
    
    # Get product details from PostgreSQL
    products = get_products_by_skus([sku])
    
    if not products:
        log_with_context(
            logger,
            "warning",
            "Product not found",
            sku=sku
        )
        raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
    
    product = products[0]
    log_with_context(
        logger,
        "info",
        "Product details retrieved successfully",
        sku=sku,
        product_name=product['name']
    )
    
    return Product(**product)

@router.get("/products/{sku}/details", response_model=ProductDetailsResponse)
def get_product_details(sku: str, recommendations_limit: int = 5):
    """
    Get comprehensive product details including related products, stock status, and actions.
    
    Args:
        sku (str): The SKU of the product to retrieve
        recommendations_limit (int): Number of related products to return (default: 5)
    
    Returns:
        ProductDetailsResponse: Comprehensive product information
    """
    log_with_context(
        logger,
        "info",
        "Getting detailed product information",
        sku=sku,
        recommendations_limit=recommendations_limit
    )
    
    # Get product details from PostgreSQL
    products = get_products_by_skus([sku])
    
    if not products:
        log_with_context(
            logger,
            "warning",
            "Product not found for detailed view",
            sku=sku
        )
        raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
    
    product_data = products[0]
    log_with_context(
        logger,
        "info",
        "Product found for detailed view",
        sku=sku,
        product_name=product_data['name']
    )
    
    # Calculate stock status
    stock_quantity = product_data['stock']
    if stock_quantity == 0:
        stock_status = 'out_of_stock'
    elif stock_quantity <= 5:
        stock_status = 'low_stock'
    else:
        stock_status = 'available'
    
    # Get related products using the same logic as recommendations
    related_products = []
    try:
        query = f"{product_data['name']} {product_data['description']}"
        embedding = get_embedding(query)
        similar_skus = search_in_qdrant(embedding, top_k=recommendations_limit + 5)
        
        # Remove the original SKU from recommendations
        filtered_skus = [s for s in similar_skus if s != sku][:recommendations_limit]
        
        # Get product details for recommendations
        if filtered_skus:
            related_products = get_products_by_skus(filtered_skus)
        
        log_with_context(
            logger,
            "info",
            "Related products found",
            sku=sku,
            related_count=len(related_products)
        )
        
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Could not get related products",
            sku=sku,
            error=str(e)
        )
        related_products = []
    
    # Create response
    product_with_status = ProductWithStatus(
        **product_data,
        stock_status=stock_status
    )
    
    metadata = ProductMetadata(
        requested_sku=sku,
        timestamp=datetime.utcnow().isoformat() + "Z",
        recommendations_count=len(related_products),
        stock_level=stock_status
    )
    
    actions = ProductActions(
        add_to_cart=stock_quantity > 0,
        request_quote=True,
        view_similar=len(related_products) > 0
    )
    
    response = ProductDetailsResponse(
        product=product_with_status,
        related_products=[Product(**p) for p in related_products],
        metadata=metadata,
        actions=actions
    )
    
    log_with_context(
        logger,
        "info",
        "Comprehensive product details response prepared",
        sku=sku,
        stock_status=stock_status,
        related_products_count=len(related_products)
    )
    
    return response

@router.get("/products", response_model=List[Product])
def get_all_products_endpoint():
    """
    Get all products from the database.
    This endpoint is used by n8n for inventory checks.
    """
    log_with_context(logger, "info", "Fetching all products for inventory check")
    
    # Retrieve all products from PostgreSQL
    products = get_all_products()
    
    if not products:
        log_with_context(logger, "warning", "No products found in the database")
        return []

    log_with_context(
        logger,
        "info",
        f"Successfully fetched {len(products)} products"
    )
    
    return [Product(**p) for p in products]
