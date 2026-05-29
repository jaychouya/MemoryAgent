from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # App
    APP_NAME: str = "MemoMind"
    DEBUG: bool = False
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    
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
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
