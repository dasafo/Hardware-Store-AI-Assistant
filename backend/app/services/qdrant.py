import os
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams, Distance, VectorParams
from app.utils.redis_client import redis_client
from app.utils.logger import logger, log_with_context

# Initialize the Qdrant client using environment variables.
# Defaults to "qdrant" host if the environment variable is not set.
client = QdrantClient(host=os.getenv("QDRANT_HOST", "qdrant"), port=6333)

# Define the name of the Qdrant collection to be used.
COLLECTION_NAME = "products"

def search_in_qdrant(embedding: list, top_k: int = 5) -> list:
    """
    Search for similar products in Qdrant using an embedding vector.
    Uses Redis caching to avoid redundant vector searches.
    
    Args:
        embedding (list): The embedding vector to search with
        top_k (int): Number of top results to return
        
    Returns:
        list: List of SKUs of the most similar products
    """
    # Check cache first
    if redis_client.is_connected():
        # Create hash of embedding for cache key
        embedding_hash = redis_client.hash_embedding(embedding)
        cached_results = redis_client.get_vector_skus(embedding_hash, top_k)
        if cached_results:
            log_with_context(
                logger,
                "info",
                "Vector search results served from cache",
                top_k=top_k,
                results_count=len(cached_results)
            )
            return cached_results
    
    log_with_context(
        logger,
        "info",
        "Performing vector search in Qdrant",
        top_k=top_k,
        embedding_dimension=len(embedding)
    )
    
    try:
        # Perform vector search
        search_result = client.search(
            collection_name="products",
            query_vector=embedding,
            limit=top_k
        )
        
        # Extract SKUs from the search results
        skus = [hit.payload["sku"] for hit in search_result]
        
        # Cache the results
        if redis_client.is_connected():
            embedding_hash = redis_client.hash_embedding(embedding)
            redis_client.set_vector_skus(embedding_hash, skus, top_k)
            log_with_context(
                logger,
                "info",
                "Vector search results cached",
                top_k=top_k,
                results_count=len(skus)
            )
        
        log_with_context(
            logger,
            "info",
            "Vector search completed successfully",
            top_k=top_k,
            results_found=len(skus),
            skus=skus[:5] if len(skus) > 5 else skus  # Log first 5 SKUs for debugging
        )
        
        return skus
        
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Vector search failed",
            top_k=top_k,
            error=str(e)
        )
        raise Exception(f"Failed to search in Qdrant: {str(e)}")

def create_collection_if_not_exists():
    """
    Create the products collection in Qdrant if it doesn't exist.
    """
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if "products" not in collection_names:
            log_with_context(
                logger,
                "info",
                "Creating products collection in Qdrant"
            )
            
            client.create_collection(
                collection_name="products",
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            
            log_with_context(
                logger,
                "info",
                "Products collection created successfully"
            )
        else:
            log_with_context(
                logger,
                "info",
                "Products collection already exists"
            )
            
    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to create/check products collection",
            error=str(e)
        )
        raise
