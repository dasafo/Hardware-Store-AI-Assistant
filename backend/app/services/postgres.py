# services/postgres.py

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from typing import List, Dict, Any, Optional
from app.utils.logger import logger, log_with_context

class PostgresService:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'hardware_store'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'password'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
            log_with_context(
                logger,
                "info",
                "PostgreSQL connection established",
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'hardware_store')
            )
        except Exception as e:
            log_with_context(
                logger,
                "error",
                "Error connecting to PostgreSQL",
                error=str(e),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                database=os.getenv('POSTGRES_DB', 'hardware_store')
            )
            raise
    
    def get_products_by_skus(self, skus: List[str]) -> List[Dict]:
        """
        Obtiene información detallada de productos por sus SKUs
        """
        if not skus:
            return []
        
        skus_placeholder = ', '.join(['%s'] * len(skus))
        
        # Consulta mejorada para ser más robusta
        query = f"""
        SELECT 
            p.sku,
            p.name,
            p.description,
            c.name as category,
            COALESCE(agg_img.image_urls[1], '') as image_url, -- Tomar la primera imagen
            COALESCE(agg_stock.total_stock, 0) as stock
        FROM products p
        LEFT JOIN category c ON p.category_id = c.id
        -- Subconsulta para agregar imágenes
        LEFT JOIN (
            SELECT 
                product_id, 
                ARRAY_AGG(url) as image_urls
            FROM images
            GROUP BY product_id
        ) as agg_img ON p.id = agg_img.product_id
        -- Subconsulta para agregar stock
        LEFT JOIN (
            SELECT 
                product_id, 
                SUM(quantity) as total_stock
            FROM stock
            GROUP BY product_id
        ) as agg_stock ON p.id = agg_stock.product_id
        WHERE p.sku IN ({skus_placeholder})
        GROUP BY p.sku, p.name, p.description, c.name, agg_img.image_urls, agg_stock.total_stock
        ORDER BY p.sku;
        """
        
        try:
            # Usar RealDictCursor para obtener resultados como diccionarios
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, skus)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except psycopg2.Error as e:
            logger.error(f"Error en la base de datos al obtener productos por SKUs: {e}")
            # Solo hacemos rollback si la conexión está abierta
            if self.connection and not self.connection.closed:
                self.connection.rollback()
            # Relanzamos la excepción para que el router la maneje como un 500
            raise e
        except Exception as e:
            logger.error(f"Error inesperado al obtener productos por SKUs: {e}")
            raise e
    
    def get_all_products(self) -> List[Dict]:
        """
        Obtiene información de todos los productos para indexación
        """
        query = """
        SELECT 
            p.sku,
            p.name,
            p.description,
            c.name as category,
            COALESCE(SUM(s.quantity), 0) as stock
        FROM products p
        LEFT JOIN category c ON p.category_id = c.id
        LEFT JOIN stock s ON p.id = s.product_id
        GROUP BY p.sku, p.name, p.description, c.name
        ORDER BY p.sku
        """
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            # Rollback the transaction in case of error
            self.connection.rollback()
            logger.error(f"Error al obtener todos los productos: {e}")
            return []
    
    def close(self):
        if self.connection:
            self.connection.close()
            log_with_context(logger, "info", "PostgreSQL connection closed")

    def search_products_by_vector_ids(self, vector_ids: List[int], limit: int = 20) -> List[Dict]:
        """Search products by vector IDs returned from Qdrant."""
        
        if not vector_ids:
            return []
        
        # Convert vector IDs back to SKUs using the same hash function
        skus = [unhash_to_sku(vid) for vid in vector_ids]
        sku_placeholders = ','.join(['%s'] * len(skus))
        
        query = f"""
        SELECT DISTINCT
            p.sku,
            p.name,
            p.description,
            p.price,
            p.brand,
            p.spec_json,
            c.name as category_name,
            COALESCE(SUM(s.quantity), 0) as total_stock,
            ARRAY_AGG(DISTINCT i.url) FILTER (WHERE i.url IS NOT NULL) as image_urls
        FROM products p
        LEFT JOIN category c ON p.category_id = c.id
        LEFT JOIN stock s ON p.id = s.product_id
        LEFT JOIN images i ON p.id = i.product_id
        WHERE p.sku IN ({sku_placeholders})
        GROUP BY p.sku, p.name, p.description, p.price, p.brand, p.spec_json, c.name
        ORDER BY 
            CASE 
                WHEN p.sku = ANY(%s) THEN array_position(%s, p.sku)
                ELSE 999999
            END
        LIMIT %s
        """
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, skus + [skus, skus, limit])
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            # Rollback the transaction in case of error
            self.connection.rollback()
            logger.error(f"Error al buscar productos por IDs de vector: {e}")
            return []

# ═══════════════════════════════════════════════════════
# GLOBAL INSTANCE AND CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════

# Global instance for convenience
_postgres_service = None

def get_postgres_service() -> PostgresService:
    """Get or create the global PostgreSQL service instance"""
    global _postgres_service
    if _postgres_service is None:
        _postgres_service = PostgresService()
    return _postgres_service

def get_products_by_skus(skus: List[str]) -> List[Dict]:
    """Convenience function to get products by SKUs"""
    return get_postgres_service().get_products_by_skus(skus)

def get_all_products() -> List[Dict]:
    """Convenience function to get all products"""
    return get_postgres_service().get_all_products()

def get_product_details(sku: str) -> Optional[Dict[str, Any]]:
    """Get detailed information for a single product by SKU"""
    products = get_products_by_skus([sku])
    return products[0] if products else None

# Application lifecycle functions
async def init_postgres(app=None):
    """Initialize PostgreSQL connection for FastAPI lifespan"""
    log_with_context(logger, "info", "Initializing PostgreSQL service")
    get_postgres_service()  # This will create the connection
    yield  # This is required for FastAPI lifespan context manager
    
async def close_postgres():
    """Close PostgreSQL connection for FastAPI lifespan"""
    global _postgres_service
    if _postgres_service:
        _postgres_service.close()
        _postgres_service = None
    log_with_context(logger, "info", "PostgreSQL service closed")

# Export convenience functions
__all__ = [
    'PostgresService',
    'get_postgres_service',
    'get_products_by_skus',
    'get_all_products', 
    'get_product_details',
    'init_postgres',
    'close_postgres'
]