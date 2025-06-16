# main.py

from fastapi import FastAPI
from app.routers import search
from app.routers import reindex_router
from app.routers import cache_router

# Create a FastAPI application instance.
app = FastAPI(
    title="Hardware Store AI Assistant",
    description="An AI-powered assistant for searching products in a hardware store.",
    version="0.1.0",
)

# Include the search router to handle search-related endpoints.
app.include_router(search.router)

# Include the reindex router to handle admin reindexing endpoints.
app.include_router(reindex_router.router)

# Include the cache router to handle cache management endpoints.
app.include_router(cache_router.router)
