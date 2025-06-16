import os
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
from typing import List

# Configure the OpenAI API key from environment variables.
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the embedding model to be used.
EMBED_MODEL = "text-embedding-3-small"

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a list of texts using the OpenAI API in a single batch.

    Args:
        texts (List[str]): The list of texts to be embedded.

    Returns:
        List[List[float]]: A list of embedding vectors for the texts.
    """
    # The OpenAI API doesn't allow empty strings, so we replace them with a single space.
    texts = [text.replace("\n", " ") for text in texts]
    texts = [text if text.strip() else ' ' for text in texts]

    response = openai.embeddings.create(input=texts, model=EMBED_MODEL)
    return [data.embedding for data in response.data]

def get_embedding(text: str) -> List[float]:
    """
    Generates an embedding for a single text by wrapping the batch function.
    
    This function uses tenacity to automatically retry in case of transient errors,
    applying an exponential backoff strategy.

    Args:
        text (str): The text to be embedded.

    Returns:
        list[float]: The embedding vector for the text.
    """
    return get_embeddings([text])[0]
