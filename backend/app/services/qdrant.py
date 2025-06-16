import os
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams

# Initialize the Qdrant client using environment variables.
# Defaults to "qdrant" host if the environment variable is not set.
client = QdrantClient(host=os.getenv("QDRANT_HOST", "qdrant"), port=6333)

# Define the name of the Qdrant collection to be used.
COLLECTION_NAME = "products"

def search_in_qdrant(vector: list[float], top_k: int = 5) -> list[str]:
    """
    Searches for similar vectors in the Qdrant collection.

    Args:
        vector (list[float]): The vector to search for.
        top_k (int): The number of similar results to return.

    Returns:
        list[str]: A list of product SKUs of the most similar items.
    """
    # Perform the search in the specified collection.
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vector,
        limit=top_k,
        search_params=SearchParams(hnsw_ef=128, exact=False),
        with_payload=True,
    )
    # Extract and return the product SKUs from the search results.
    return [result.id for result in search_results]
