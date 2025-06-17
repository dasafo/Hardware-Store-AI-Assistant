import sys
sys.path.append('/app')
from app.services.embeddings import get_embedding

try:
    embedding = get_embedding('test')
    print(f'Vector size: {len(embedding)}')
    print(f'First 5 values: {embedding[:5]}')
except Exception as e:
    print(f'Error: {e}') 