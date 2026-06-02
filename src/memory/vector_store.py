"""Vector store for semantic search."""

import logging
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """A document with embedding vector."""
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """In-memory vector store for semantic search."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.documents: Dict[str, VectorDocument] = {}
        self.embeddings: List[List[float]] = []
        self.ids: List[str] = []
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID for text."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_np = np.array(a)
        b_np = np.array(b)
        
        dot_product = np.dot(a_np, b_np)
        norm_a = np.linalg.norm(a_np)
        norm_b = np.linalg.norm(b_np)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def add(
        self,
        text: str,
        embedding: List[float],
        metadata: Dict[str, Any] = None,
        id: str = None
    ) -> str:
        """Add a document to the store."""
        doc_id = id or self._generate_id(text)
        
        doc = VectorDocument(
            id=doc_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        self.documents[doc_id] = doc
        self.embeddings.append(embedding)
        self.ids.append(doc_id)
        
        logger.debug(f"Added document: {doc_id}")
        return doc_id
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.embeddings:
            return []
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            similarities.append((similarity, self.ids[i]))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top-k results
        results = []
        for similarity, doc_id in similarities[:top_k]:
            doc = self.documents[doc_id]
            results.append({
                "id": doc_id,
                "text": doc.text,
                "score": similarity,
                "metadata": doc.metadata
            })
        
        return results
    
    def delete(self, id: str) -> bool:
        """Delete a document."""
        if id not in self.documents:
            return False
        
        del self.documents[id]
        
        # Remove from embeddings list
        idx = self.ids.index(id)
        self.ids.pop(idx)
        self.embeddings.pop(idx)
        
        logger.debug(f"Deleted document: {id}")
        return True
    
    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        if id not in self.documents:
            return None
        
        doc = self.documents[id]
        return {
            "id": doc.id,
            "text": doc.text,
            "metadata": doc.metadata
        }
    
    def size(self) -> int:
        """Get number of documents."""
        return len(self.documents)
    
    def clear(self):
        """Clear all documents."""
        self.documents.clear()
        self.embeddings.clear()
        self.ids.clear()


class HybridRetriever:
    """Combines vector search with keyword search."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    async def retrieve(
        self,
        query: str,
        query_embedding: List[float],
        keyword_results: List[Dict],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve using hybrid approach."""
        # Vector search
        vector_results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Combine results
        combined = {}
        
        # Add vector results with score
        for result in vector_results:
            doc_id = result["id"]
            combined[doc_id] = {
                **result,
                "vector_score": result["score"],
                "keyword_score": 0.0
            }
        
        # Add keyword results with score
        for result in keyword_results:
            doc_id = result.get("id", "")
            if doc_id in combined:
                combined[doc_id]["keyword_score"] = result.get("score", 1.0)
            else:
                combined[doc_id] = {
                    **result,
                    "vector_score": 0.0,
                    "keyword_score": result.get("score", 1.0)
                }
        
        # Calculate combined score (weighted average)
        for doc_id in combined:
            vector_score = combined[doc_id].get("vector_score", 0.0)
            keyword_score = combined[doc_id].get("keyword_score", 0.0)
            combined[doc_id]["score"] = (vector_score * 0.7) + (keyword_score * 0.3)
        
        # Sort by combined score
        results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
