"""Memory chunker for splitting long content into manageable pieces."""

import re
from typing import List


class MemoryChunker:
    """
    Split memory content into chunks.
    
    Inspired by Memory Tree's approach:
    - Normalize data into ~3k token chunks
    - Preserve sentence boundaries
    - Maintain context between chunks
    """
    
    def __init__(self, max_tokens: int = 3000):
        """
        Initialize chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (approximate)
        """
        self.max_chars = max_tokens * 2  # 粗略估计：1 token ≈ 2 字符
    
    def chunk(self, content: str) -> List[str]:
        """
        Split content into chunks.
        
        Args:
            content: Content to split
            
        Returns:
            List of content chunks
        """
        if len(content) <= self.max_chars:
            return [content]
        
        chunks = []
        current_chunk = ""
        
        # 按句子分割
        sentences = re.split(r'([。！？.!?])', content)
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            # 加上标点符号
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            
            # 检查是否超过限制
            if len(current_chunk) + len(sentence) > self.max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
