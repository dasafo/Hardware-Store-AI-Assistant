# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routers import search, recommend, reindex_router, cache_router, chat

# Create a FastAPI application instance.
app = FastAPI(
    title="Hardware Store AI Assistant",
    description="API for searching products in a hardware store using vector similarity search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the search router to handle search-related endpoints.
app.include_router(search.router)

# Include the recommend router to handle recommendation endpoints.
app.include_router(recommend.router)

# Include the chat router to handle chat-related endpoints.
app.include_router(chat.router)

# Include the reindex router to handle admin reindexing endpoints.
app.include_router(reindex_router.router)

# Include the cache router to handle cache management endpoints.
app.include_router(cache_router.router)

@app.get("/")
def read_root():
    return {"message": "Hardware Store AI Assistant API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
