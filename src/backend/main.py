from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.backend.api import chat, memory, integrations
from src.backend.auth import APIKeyMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MemoMind API",
    description="Personal AI Assistant with Cognitive Memory Architecture",
    version="0.1.0"
)

app.add_middleware(APIKeyMiddleware)
_LOCAL_ORIGIN_RE = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_LOCAL_ORIGIN_RE,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(memory.router, prefix="/api", tags=["memory"])
app.include_router(integrations.router, prefix="/api", tags=["integrations"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from src.backend.auth import is_auth_enabled

    return {
        "status": "healthy",
        "service": "MemoMind",
        "version": "0.1.0",
        "auth_required": is_auth_enabled(),
    }
