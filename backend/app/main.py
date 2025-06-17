# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from contextlib import asynccontextmanager

from .routers import search, recommendations, reindex_router, cache_router, chat, health, security, notifications, inventory
from .middleware.logging_middleware import LoggingMiddleware
from .middleware.security_middleware import SecurityMiddleware
from .services.postgres import init_postgres
from .utils.logger import logger, log_with_context
from .utils.metrics import metrics

# Create a FastAPI application instance.
app = FastAPI(
    title="Hardware Store AI Assistant",
    description="API for searching products in a hardware store using vector similarity search",
    version="1.0.0",
    lifespan=init_postgres
)

# Add logging middleware (should be first)
app.add_middleware(SecurityMiddleware)
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the health router first for monitoring
app.include_router(health.router)

# Include the search router to handle search-related endpoints.
app.include_router(search.router)

# Include the recommend router to handle recommendation endpoints.
app.include_router(recommendations.router)

# Include the chat router to handle chat-related endpoints.
app.include_router(chat.router)

# Include the reindex router to handle admin reindexing endpoints.
app.include_router(reindex_router.router)

# Include the cache router to handle cache management endpoints.
app.include_router(cache_router.router)

# Include the security router to handle security-related endpoints.
app.include_router(security.router)

# Include the notifications router
app.include_router(notifications.router)

# Include the inventory router
app.include_router(inventory.router)

@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    log_with_context(
        logger,
        "info",
        "Hardware Store AI Assistant starting up",
        version="1.0.0",
        environment="production"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    log_with_context(
        logger,
        "info",
        "Hardware Store AI Assistant shutting down"
    )

@app.get("/")
def read_root():
    """Root endpoint with basic API information"""
    log_with_context(logger, "info", "Root endpoint accessed")
    return {
        "message": "Hardware Store AI Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "recommend": "/recommend",
            "chat": "/chat"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
