#!/usr/bin/env python3

import logging
from app.utils.db import get_connection
from qdrant_client import QdrantClient, models
from app.services.qdrant import create_collection_if_not_exists
from app.services.embeddings import get_embeddings
import hashlib

COLLECTION_NAME = 'products'
BATCH_SIZE = 16

def sku_to_id(sku):
    """Convert SKU string to a valid integer ID for Qdrant"""
    # Use hash to convert SKU to integer
    return int(hashlib.md5(sku.encode()).hexdigest()[:8], 16)

def get_all_products(cursor):
    cursor.execute("SELECT sku, name, description FROM products")
    while True:
        records = cursor.fetchmany(BATCH_SIZE)
        if not records:
            break
        yield records

def main():
    print('Starting Qdrant indexing process...')
    
    # Connect to Qdrant
    client = QdrantClient(host='qdrant', port=6333, check_compatibility=False)
    
    # Check if collection exists, create if not
    try:
        existing_collections = client.get_collections()
        collection_exists = any(c.name == COLLECTION_NAME for c in existing_collections.collections)
        
        if collection_exists:
            print(f'Collection {COLLECTION_NAME} already exists.')
        else:
            print(f'Creating collection {COLLECTION_NAME} with on-disk storage and quantization...')
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE,
                    on_disk=True,
                ),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        always_ram=True,
                    ),
                ),
            )
            print(f'Collection {COLLECTION_NAME} created successfully.')
    except Exception as e:
        print(f'Error with collection: {e}')
        return
    
    # Index products
    with get_connection() as conn, conn.cursor() as cursor:
        product_count = 0
        batch_count = 0
        
        for batch in get_all_products(cursor):
            batch_count += 1
            print(f'Processing batch {batch_count}...')
            
            # Convert SKUs to valid integer IDs and create payloads with original SKUs
            point_ids = [sku_to_id(record[0]) for record in batch]
            texts_to_embed = [f"{record[1]}: {record[2]}" for record in batch]
            payloads = [{"sku": record[0], "name": record[1], "description": record[2]} for record in batch]
            
            try:
                embeddings = get_embeddings(texts_to_embed)
                
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=models.Batch(
                        ids=point_ids,
                        vectors=embeddings,
                        payloads=payloads
                    ),
                    wait=True
                )
                
                product_count += len(batch)
                print(f'Successfully indexed batch {batch_count}. Total products: {product_count}')
                
            except Exception as e:
                print(f'Error processing batch {batch_count}: {e}')
                continue
    
    print(f'Qdrant indexing process finished successfully. Total products indexed: {product_count}')

if __name__ == '__main__':
    main()