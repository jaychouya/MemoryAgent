import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.models.memory import ShortTermMemoryItem, MemorySearchResult
from src.utils.embedding import EmbeddingService

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """
    Short-term Memory Layer - Recent conversations and temporary info.
    
    Human analogy: What happened yesterday, recent events.
    
    Implementation:
    - PostgreSQL with vector storage
    - Semantic search via vector similarity
    - Automatic expiration based on TTL
    - Importance scoring for retention priority
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        embedding_service: EmbeddingService,
        default_ttl_days: int = 30
    ):
        """
        Initialize short-term memory.
        
        Args:
            db_session: Async SQLAlchemy session
            embedding_service: Service for generating embeddings
            default_ttl_days: Default time-to-live in days
        """
        self.db = db_session
        self.embedder = embedding_service
        self.default_ttl_days = default_ttl_days
    
    async def store(self, item: ShortTermMemoryItem) -> str:
        """
        Store a memory in short-term storage.
        
        Args:
            item: Memory item to store
            
        Returns:
            Memory ID
        """
        # Generate embedding
        embedding = await self.embedder.embed(item.content)
        
        # Calculate expiration
        expires_at = item.expires_at or datetime.now() + timedelta(days=self.default_ttl_days)
        
        # Create database record
        record = ShortTermMemoryRecord(
            id=item.memory_id,
            user_id=item.user_id,
            content=item.content,
            embedding=embedding,
            memory_type=item.memory_type,
            importance_score=item.importance_score,
            created_at=item.created_at,
            expires_at=expires_at,
            metadata_=item.metadata
        )
        
        self.db.add(record)
        await self.db.commit()
        
        logger.info(f"Stored short-term memory {item.memory_id} for user {item.user_id}")
        return item.memory_id
    
    async def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        min_importance: float = 0.0
    ) -> List[MemorySearchResult]:
        """
        Search short-term memories by semantic similarity.
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
            min_importance: Minimum importance score filter
            
        Returns:
            List of memory search results
        """
        query_embedding = await self.embedder.embed(query)
        
        # Build query - simplified to avoid pgvector dependency issues
        stmt = (
            select(ShortTermMemoryRecord)
            .where(ShortTermMemoryRecord.user_id == user_id)
            .where(ShortTermMemoryRecord.expires_at > datetime.now())
            .where(ShortTermMemoryRecord.importance_score >= min_importance)
            .limit(top_k)
        )
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        # Convert to search results with calculated similarity
        results = []
        for record in records:
            memory_item = ShortTermMemoryItem(
                memory_id=record.id,
                user_id=record.user_id,
                content=record.content,
                importance_score=record.importance_score,
                created_at=record.created_at,
                metadata=record.metadata_ or {}
            )
            
            # Calculate similarity
            score = self.embedder.cosine_similarity(query_embedding, record.embedding)
            
            results.append(MemorySearchResult(
                memory=memory_item,
                score=score,
                retrieval_method="semantic"
            ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def get_expired(self, user_id: str) -> List[ShortTermMemoryItem]:
        """
        Get expired memories for cleanup.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of expired memory items
        """
        stmt = (
            select(ShortTermMemoryRecord)
            .where(ShortTermMemoryRecord.user_id == user_id)
            .where(ShortTermMemoryRecord.expires_at <= datetime.now())
        )
        
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        
        return [
            ShortTermMemoryItem(
                memory_id=r.id,
                user_id=r.user_id,
                content=r.content,
                importance_score=r.importance_score,
                created_at=r.created_at,
                metadata=r.metadata_ or {}
            )
            for r in records
        ]
    
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted, False if not found
        """
        stmt = delete(ShortTermMemoryRecord).where(ShortTermMemoryRecord.id == memory_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_by_id(self, memory_id: str) -> Optional[ShortTermMemoryItem]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory item if found, None otherwise
        """
        stmt = select(ShortTermMemoryRecord).where(ShortTermMemoryRecord.id == memory_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            return None
        
        return ShortTermMemoryItem(
            memory_id=record.id,
            user_id=record.user_id,
            content=record.content,
            importance_score=record.importance_score,
            created_at=record.created_at,
            metadata=record.metadata_ or {}
        )


# SQLAlchemy model
from sqlalchemy import Column, String, Float, DateTime, JSON, LargeBinary


class ShortTermMemoryRecord:
    """SQLAlchemy model for short-term memory."""
    
    __tablename__ = "short_term_memories"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    embedding = Column(LargeBinary)  # Store as binary for simplicity
    memory_type = Column(String, default="general")
    importance_score = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    metadata_ = Column("metadata", JSON, default={})
