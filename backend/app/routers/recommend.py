# routers/recommend.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.models.product import SearchResponse, Product
from app.services.embeddings import get_embedding
from app.services.qdrant import search_in_qdrant
from app.services.postgres import get_products_by_ids

router = APIRouter()

class RecommendRequest(BaseModel):
    sku: str
    limit: int = 5

class RecommendResponse(BaseModel):
    recommendations: List[dict]

@router.post("/recommend", response_model=RecommendResponse)
def get_recommendations(request: RecommendRequest):
    """
    Get product recommendations based on a given SKU.
    
    Args:
        request (RecommendRequest): The request containing SKU and limit
    
    Returns:
        RecommendResponse: A list of recommended products
    """
    print(f"🎯 Getting recommendations for SKU: {request.sku}")
    
    try:
        # First, get the product details for the given SKU
        products = get_products_by_ids([request.sku])
        
        if not products:
            raise HTTPException(status_code=404, detail=f"Product with SKU {request.sku} not found")
        
        base_product = products[0]
        
        # Use the product name and description to find similar products
        query = f"{base_product['name']} {base_product['description']}"
        
        # Generate embedding for the product
        embedding = get_embedding(query)
        
        # Search for similar products
        similar_skus = search_in_qdrant(embedding, top_k=request.limit + 5)  # Get more to filter out the original
        
        # Remove the original SKU from recommendations
        filtered_skus = [sku for sku in similar_skus if sku != request.sku][:request.limit]
        
        # Get product details for recommendations
        recommendations = get_products_by_ids(filtered_skus)
        
        print(f"✅ Found {len(recommendations)} recommendations")
        
        return RecommendResponse(recommendations=recommendations)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}") 