from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # App
    APP_NAME: str = "MemoMind"
    DEBUG: bool = False
    MEMORYAGENT_API_KEY: Optional[str] = Field(
        default=None,
        description="When set, /api/* requires X-API-Key or Bearer token",
    )
    MEMORYAGENT_WEBHOOK_INBOUND_TOKEN: Optional[str] = Field(
        default=None,
        description="Optional shared secret for /api/webhooks/* (?token=)",
    )
    MEMORYAGENT_MCP_HTTP_URL: str = Field(
        default="http://127.0.0.1:8000",
        description="Base URL for MCP tools calling HTTP sidecar (optional)",
    )
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    LLM_API_KEY: Optional[str] = Field(
        default=None,
        description="Default chat model API key (e.g. Xiaomi MiMo)",
    )
    LLM_BASE_URL: str = Field(
        default="https://token-plan-cn.xiaomimimo.com/v1",
        description="Default chat model base URL",
    )
    LLM_MODEL: str = Field(
        default="mimo-v2.5-pro",
        description="Default chat model name",
    )
    
    # Redis (Working Memory)
    REDIS_URL: str = "redis://localhost:6379"
    WORKING_MEMORY_TTL: int = 3600  # 1 hour
    
    # PostgreSQL (Short-term + Episodic Memory)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/memomind"
    
    # Chroma (Long-term Memory)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "long_term_memory"
    
    # Memory Settings
    SHORT_TERM_MEMORY_DAYS: int = 30
    MAX_CONTEXT_MESSAGES: int = 20
    MEMORY_CONSOLIDATION_INTERVAL: int = 3600  # 1 hour
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 384

    RERANK_ENABLED: bool = True
    RERANK_CANDIDATE_POOL: int = 12
    RERANK_EMBED_CAP: int = 8
    RERANK_USE_LLM: bool = False
    MEMORY_RECALL_FAST: bool = Field(
        default=True,
        description="Chat hot path: skip LLM rerank, smaller pool, enrich only top-k",
    )
    MEMORY_CONFLICT_UI: bool = Field(
        default=True,
        description="Surface memory conflicts to UI instead of silent auto-supersede",
    )

    MEMORY_EXTRACT_ENABLED: bool = True
    MEMORY_EXTRACT_LLM_MIN_CHARS: int = Field(
        default=200,
        description="Only call LLM extractor when user+assistant text length >= this (L1 regex always runs)",
    )
    MEMORY_OBSERVER_ASYNC: bool = Field(
        default=True,
        description="Run post-turn memory write in background; do not block chat response",
    )
    MEMORY_QUERY_REWRITE_ENABLED: bool = True
    MEMORY_QUERY_REWRITE_MIN_LEN: int = 80
    MEMORY_QUERY_REWRITE_MAX_LEN: int = 120
    PROVENANCE_ENABLED: bool = True
    SYMBOLIC_MEMORY_ENABLED: bool = True
    SYMBOLIC_MEMORY_MIN_TOOLS: int = 3
    CCR_ENABLED: bool = True
    CCR_STORAGE_DIR: str = "memories"
    CCR_OFFLOAD_THRESHOLD: int = 8192
    CCR_PREVIEW_CHARS: int = 4096
    RECALL_EVAL_MIN: float = 0.9
    
    # Decision Engine Settings
    AUTONOMOUS_ACTIONS: List[str] = [
        "memory_search",
        "context_retrieval",
        "response_generation",
        "memory_consolidation"
    ]
    CONFIRM_REQUIRED_ACTIONS: List[str] = [
        "memory_delete",
        "preference_update",
        "external_api_call"
    ]
    FORBIDDEN_ACTIONS: List[str] = [
        "financial_transaction",
        "personal_data_export"
    ]


# Global settings instance
settings = Settings()
