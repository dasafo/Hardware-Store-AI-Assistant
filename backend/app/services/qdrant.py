import os
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams
from app.utils.redis_client import redis_client

# Initialize the Qdrant client using environment variables.
# Defaults to "qdrant" host if the environment variable is not set.
client = QdrantClient(host=os.getenv("QDRANT_HOST", "qdrant"), port=6333)

# Define the name of the Qdrant collection to be used.
COLLECTION_NAME = "products"

def search_in_qdrant(vector: list[float], top_k: int = 5) -> list[str]:
    """
    Searches for similar vectors in the Qdrant collection with Redis caching.

    Args:
        vector (list[float]): The vector to search for.
        top_k (int): The number of similar results to return.

    Returns:
        list[str]: A list of product SKUs of the most similar items.
    """
    # Check cache first
    if redis_client.is_connected():
        embedding_hash = redis_client.hash_embedding(vector)
        cached_skus = redis_client.get_vector_skus(embedding_hash, top_k)
        if cached_skus:
            print(f"⚡ Vector search served from cache ({len(cached_skus)} SKUs)")
            return cached_skus
    
    # Perform the search in the specified collection.
    print(f"🔍 Performing vector search in Qdrant")
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=top_k,
        search_params=SearchParams(hnsw_ef=128, exact=False),
        with_payload=True,
    )
    
    # Extract SKUs from the search results
    skus = [result.payload.get("sku") for result in search_results if result.payload and result.payload.get("sku")]
    
    # Cache the results
    if redis_client.is_connected() and skus:
        embedding_hash = redis_client.hash_embedding(vector)
        redis_client.set_vector_skus(embedding_hash, skus, top_k)
    
    return skus
