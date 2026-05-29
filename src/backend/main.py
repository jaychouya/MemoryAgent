from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.backend.api import chat, memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MemoMind API",
    description="Personal AI Assistant with Cognitive Memory Architecture",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(memory.router, prefix="/api", tags=["memory"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MemoMind",
        "version": "0.1.0"
    }
