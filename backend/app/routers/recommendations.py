from fastapi import APIRouter, HTTPException
from app.models.product import RecommendationsRequest, RecommendationsResponse, Product, RecommendationsMetadata
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_skus
from app.utils.logger import logger, log_with_context
from datetime import datetime
import time

router = APIRouter()

@router.post("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(payload: RecommendationsRequest):
    """
    Get product recommendations based on a product SKU.
    
    Args:
        payload (RecommendationsRequest): The request containing the SKU and optional limit.
    
    Returns:
        RecommendationsResponse: A list of recommended products.
    """
    start_time = time.time()
    sku = payload.sku
    limit = payload.limit
    
    log_with_context(
        logger,
        "info",
        "Getting recommendations for product",
        sku=sku,
        limit=limit
    )
    
    # 1. Get the product details for the given SKU
    products = get_products_by_skus([sku])
    if not products:
        log_with_context(
            logger,
            "warning",
            "Product not found for recommendations",
            sku=sku
        )
        raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
    
    product = products[0]
    log_with_context(
        logger,
        "info",
        "Product found for recommendations",
        sku=sku,
        product_name=product['name']
    )
    
    # 2. Create a query based on the product name and description
    query = f"{product['name']} {product['description']}"
    
    # 3. Generate an embedding for the query
    embedding = get_embedding(query)
    
    # 4. Search for similar products in Qdrant, getting more than needed to filter out the original
    similar_skus = search_in_qdrant(embedding, top_k=limit + 5)
    
    # 5. Filter out the original SKU from the recommendations
    recommended_skus = [s for s in similar_skus if s != sku][:limit]
    
    log_with_context(
        logger,
        "info",
        "Similar products found in vector search",
        sku=sku,
        similar_skus_count=len(similar_skus),
        recommended_skus_count=len(recommended_skus)
    )
    
    # 6. Get the full product details for the recommended SKUs
    recommended_products = get_products_by_skus(recommended_skus)
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    # Create metadata
    metadata = RecommendationsMetadata(
        requested_sku=sku,
        timestamp=datetime.utcnow().isoformat() + "Z",
        recommendations_count=len(recommended_products),
        processing_time_ms=round(processing_time, 2),
        similar_products_found=len(similar_skus)
    )
    
    log_with_context(
        logger,
        "info",
        "Recommendations retrieved successfully",
        sku=sku,
        recommendations_count=len(recommended_products)
    )
    
    return RecommendationsResponse(
        recommendations=[Product(**p) for p in recommended_products],
        metadata=metadata,
        status="success"
    ) 