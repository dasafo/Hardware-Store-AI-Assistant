# main.py

from fastapi import FastAPI
from app.routers import search

# Create a FastAPI application instance.
app = FastAPI(
    title="Hardware Store AI Assistant",
    description="An AI-powered assistant for searching products in a hardware store.",
    version="0.1.0",
)

# Include the search router to handle search-related endpoints.
app.include_router(search.router)
