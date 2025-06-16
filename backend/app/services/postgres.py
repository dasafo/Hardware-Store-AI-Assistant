# services/postgres.py

from app.utils.db import get_connection
from typing import List, Dict

def get_products_by_ids(product_skus: List[str]) -> List[Dict]:
    """
    Retrieves product details from the PostgreSQL database for a given list of product SKUs.

    Args:
        product_skus (List[str]): A list of product SKUs.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents a product.
    """
    # Return an empty list if no product SKUs are provided.
    if not product_skus:
        return []
    
    # Create a string of placeholders for the SQL query.
    placeholders = ','.join(['%s'] * len(product_skus))

    # Formulate the SQL query to fetch product details.
    query = f"""
        SELECT 
            p.sku, 
            p.name, 
            p.description, 
            c.name AS category,
            ri.url AS image_url, 
            s.quantity AS stock
        FROM product p
        LEFT JOIN category c ON p.category_id = c.category_id
        LEFT JOIN representative_images ri ON p.sku = ri.sku
        LEFT JOIN stock_location s ON p.sku = s.sku
        WHERE p.sku IN ({placeholders})
    """

    # Establish a connection to the database.
    with get_connection() as conn:
        # Create a new cursor to execute the query.
        with conn.cursor() as cur:
            # Execute the query with the list of product SKUs.
            cur.execute(query, product_skus)
            
            # Fetch all rows from the query result.
            rows = cur.fetchall()
            
            # Get the column names from the cursor description.
            columns = [desc[0] for desc in cur.description]
            
            # Create a list of dictionaries from the rows and columns.
            return [dict(zip(columns, row)) for row in rows]


def get_all_products() -> list[dict]:
    """Get all products from the database."""
    query = """
        SELECT p.sku, p.name, p.description, c.name AS category
        FROM product p
        LEFT JOIN category c ON p.category_id = c.category_id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]