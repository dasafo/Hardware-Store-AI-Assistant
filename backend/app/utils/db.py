import os
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_connection():
    """
    Establishes and manages a connection to the PostgreSQL database.

    This function is a context manager that handles the connection lifecycle,
    ensuring that the connection is closed after use. It reads the database
    credentials from environment variables.

    Yields:
        psycopg2.connection: A connection object to the database.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT", 5432),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
        yield connection
    finally:
        if connection:
            connection.close()
