import os
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
from typing import List
from app.utils.redis_client import redis_client

# Configure the OpenAI API key from environment variables.
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the embedding model to be used.
EMBED_MODEL = "text-embedding-3-small"

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of texts using the OpenAI API with Redis caching.

    Args:
        texts (List[str]): The list of texts to be embedded.

    Returns:
        List[List[float]]: A list of embedding vectors for the texts.
    """
    # The OpenAI API doesn't allow empty strings, so we replace them with a single space.
    cleaned_texts = [text.replace("\n", " ") for text in texts]
    cleaned_texts = [text if text.strip() else ' ' for text in cleaned_texts]
    
    # Check cache for each text
    embeddings = []
    texts_to_embed = []
    cache_indices = []
    
    for i, text in enumerate(cleaned_texts):
        if redis_client.is_connected():
            cached_embedding = redis_client.get_embedding(text)
            if cached_embedding:
                embeddings.append(cached_embedding)
                continue
        
        # Need to embed this text
        texts_to_embed.append(text)
        cache_indices.append(i)
        embeddings.append(None)  # Placeholder
    
    # Generate embeddings for uncached texts
    if texts_to_embed:
        print(f"🔄 Generating {len(texts_to_embed)} embeddings (cache missed)")
        response = openai.embeddings.create(input=texts_to_embed, model=EMBED_MODEL)
        new_embeddings = [data.embedding for data in response.data]
        
        # Store in cache and update results
        for i, embedding in enumerate(new_embeddings):
            original_index = cache_indices[i]
            embeddings[original_index] = embedding
            
            # Cache the embedding
            if redis_client.is_connected():
                redis_client.set_embedding(texts_to_embed[i], embedding)
    else:
        print(f"⚡ All {len(texts)} embeddings served from cache")
    
    return embeddings

def get_embedding(text: str) -> List[float]:
    """
    Generates an embedding for a single text with Redis caching.
    
    This function uses tenacity to automatically retry in case of transient errors,
    applying an exponential backoff strategy.

    Args:
        text (str): The text to be embedded.

    Returns:
        list[float]: The embedding vector for the text.
    """
    # Check cache first
    if redis_client.is_connected():
        cached_embedding = redis_client.get_embedding(text)
        if cached_embedding:
            print(f"⚡ Embedding served from cache")
            return cached_embedding
    
    # Generate and cache embedding
    print(f"🔄 Generating new embedding")
    embedding = get_embeddings([text])[0]
    
    # Cache the result
    if redis_client.is_connected():
        redis_client.set_embedding(text, embedding)
    
    return embedding
