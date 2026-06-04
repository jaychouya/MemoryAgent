"""SQLite-backed persistent vector storage."""

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np

from src.memory.embeddings import embed_text, local_embed
from src.utils.config import settings
from src.memory.vector_store import VectorStore

logger = logging.getLogger(__name__)

EMBED_DIM = settings.EMBEDDING_DIMENSIONS or 384


def _blob_from_embedding(embedding: List[float]) -> bytes:
    arr = np.array(embedding, dtype=np.float32)
    return arr.tobytes()


def _embedding_from_blob(blob: bytes, dimension: int) -> List[float]:
    arr = np.frombuffer(blob, dtype=np.float32)
    if len(arr) != dimension:
        arr = np.frombuffer(blob, dtype=np.float64).astype(np.float32)
    return arr.tolist()


class PersistentVectorStore:
    def __init__(self, db_path: str, dimension: int = EMBED_DIM):
        self.db_path = db_path
        self.dimension = dimension
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self.memory_store = VectorStore(dimension=dimension)
        self.load_into_memory()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_schema(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_vectors (
                    memory_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    dimension INTEGER NOT NULL,
                    user_id TEXT,
                    memory_type TEXT,
                    content TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def upsert(
        self,
        memory_id: str,
        content: str,
        user_id: str = None,
        memory_type: str = "user",
        embedding: List[float] = None,
    ):
        emb = embedding or embed_text(content)
        blob = _blob_from_embedding(emb)
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_vectors
                (memory_id, embedding, dimension, user_id, memory_type, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (memory_id, blob, self.dimension, user_id, memory_type, content),
            )
            conn.commit()
        self.memory_store.add(
            text=content,
            embedding=emb,
            metadata={"user_id": user_id, "memory_type": memory_type},
            id=memory_id,
        )

    def delete(self, memory_id: str):
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM memory_vectors WHERE memory_id = ?",
                (memory_id,),
            )
            conn.commit()
        self.memory_store.delete(memory_id)

    def load_into_memory(self):
        self.memory_store.clear()
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM memory_vectors").fetchall()
            for row in rows:
                emb = _embedding_from_blob(row["embedding"], row["dimension"])
                self.memory_store.add(
                    text=row["content"] or "",
                    embedding=emb,
                    metadata={
                        "user_id": row["user_id"],
                        "memory_type": row["memory_type"],
                    },
                    id=row["memory_id"],
                )
        logger.info(f"Loaded {self.memory_store.size()} vectors from {self.db_path}")

    def backfill_from_index_rows(self, rows: List[Dict]):
        for row in rows:
            mid = row.get("memory_id")
            content = row.get("content", "")
            if not mid or not content:
                continue
            if self.memory_store.get(mid):
                continue
            self.upsert(
                memory_id=mid,
                content=content,
                user_id=row.get("user_id"),
                memory_type=row.get("memory_type", "user"),
            )

    def get_vector_store(self) -> VectorStore:
        return self.memory_store
