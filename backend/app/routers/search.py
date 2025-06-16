# routers/search.py

from fastapi import APIRouter
from app.models.product import SearchRequest, SearchResponse, Product
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_ids
from app.utils.redis_client import redis_client

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
            print(f"⚡ Complete search results served from cache")
            return {"results": [Product(**p) for p in cached_results]}
    
    print(f"🔍 Processing search query: '{query}'")
    
    # 2. Generate an embedding from the user's search query (with embedding cache)
    embedding = get_embedding(query)
    
    # 3. Use the embedding to find the SKUs of the most similar products in Qdrant (with vector cache)
    skus = search_in_qdrant(embedding, top_k=top_k)
    
    # 4. Retrieve the full product details from PostgreSQL using the SKUs found
    products = get_products_by_ids(skus)
    
    # 5. Cache the complete search results
    if redis_client.is_connected() and products:
        redis_client.set_search_results(query, products, top_k)
        print(f"💾 Cached complete search results")
    
    # 6. Return the products found
    return {"results": [Product(**p) for p in products]}
