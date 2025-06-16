# routers/buscar.py

from fastapi import APIRouter
from app.models.product import SearchRequest, SearchResponse, Product
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_ids

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
def search_products(payload: SearchRequest):
    """
    Search for products in the database.

    Args:
        payload (SearchRequest): The search request containing the user's query.

    Returns:
        SearchResponse: A list of matching products.
    """
    # 1. Generate an embedding from the user's search query.
    embedding = get_embedding(payload.query)
    
    # 2. Use the embedding to find the SKUs of the most similar products in Qdrant.
    skus = search_in_qdrant(embedding, top_k=5)
    
    # 3. Retrieve the full product details from PostgreSQL using the SKUs found.
    products = get_products_by_ids(skus)
    
    # 4. Return the products found.
    return {"results": [Product(**p) for p in products]}
