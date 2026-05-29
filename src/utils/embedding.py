import logging
from typing import List
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding service for text vectorization.
    
    Uses OpenAI's embedding model to convert text to vectors.
    """
    
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536
    ):
        """
        Initialize embedding service.
        
        Args:
            client: AsyncOpenAI client instance
            model: Embedding model name
            dimensions: Output vector dimensions
        """
        self.client = client
        self.model = model
        self.dimensions = dimensions
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text.strip(),
                dimensions=self.dimensions
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text of length {len(text)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t.strip() for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                dimensions=self.dimensions
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Similarity score between -1 and 1
        """
        import numpy as np
        
        a = np.array(vec1)
        b = np.array(vec2)
        
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
