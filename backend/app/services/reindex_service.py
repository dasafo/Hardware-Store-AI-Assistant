#!/usr/bin/env python3

from typing import List, Optional
from qdrant_client import QdrantClient, models
from app.utils.db import get_connection
from app.services.embeddings import get_embeddings
import hashlib
import asyncio
import time
import logging

COLLECTION_NAME = 'products'
BATCH_SIZE = 16

def sku_to_id(sku):
    """Convert SKU string to a valid integer ID for Qdrant"""
    return int(hashlib.md5(sku.encode()).hexdigest()[:8], 16)

def get_products_by_skus(skus: List[str]) -> List[dict]:
    """Get specific products by their SKUs"""
    if not skus:
        return []
    
    placeholders = ','.join(['%s'] * len(skus))
    query = f"SELECT sku, name, description FROM products WHERE sku IN ({placeholders})"
    
    with get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(query, skus)
        rows = cursor.fetchall()
        return [{"sku": row[0], "name": row[1], "description": row[2]} for row in rows]

def get_all_products_for_reindex() -> List[dict]:
    """Get all products for reindexing"""
    query = "SELECT sku, name, description FROM products"
    
    with get_connection() as conn, conn.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        return [{"sku": row[0], "name": row[1], "description": row[2]} for row in rows]

def reindex_products(req):
    """Reindex all products or specific SKUs"""
    print(f'Starting reindex process...')
    
    # Connect to Qdrant
    client = QdrantClient(host='qdrant', port=6333, check_compatibility=False)
    
    # Determine which products to reindex
    if req.force_full or req.skus is None:
        products = get_all_products_for_reindex()
        print(f'Full reindex: processing {len(products)} products')
    else:
        products = get_products_by_skus(req.skus)
        print(f'Incremental reindex: processing {len(products)} specific products')
    
    if not products:
        print('No products to reindex')
        return
    
    # Process products in batches
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        
        try:
            print(f'Processing batch {batch_num}...')
            
            # Prepare data for Qdrant
            point_ids = [sku_to_id(prod["sku"]) for prod in batch]
            texts_to_embed = [f"{prod['name']}: {prod['description']}" for prod in batch]
            payloads = [{"sku": prod["sku"], "name": prod["name"], "description": prod["description"]} for prod in batch]
            
            # Generate embeddings
            embeddings = get_embeddings(texts_to_embed)
            
            # Upsert to Qdrant
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=models.Batch(
                    ids=point_ids,
                    vectors=embeddings,
                    payloads=payloads
                ),
                wait=True
            )
            
            print(f'Successfully processed batch {batch_num}')
            
        except Exception as e:
            print(f'Error processing batch {batch_num}: {e}')
            continue
    
    print(f'Reindex process completed successfully') 