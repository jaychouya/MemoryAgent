"""
Five-step context compression for MemoryAI Agent.

Implements Claude Code's progressive compression strategy:
1. Large results to disk (zero info loss)
2. Snip old messages (low info loss)
3. Micro-compact old tool outputs (medium info loss)
4. Context collapse (read-time projection)
5. Full summary (high info loss)

Key principle: "能轻则轻，逐步加码" (Use lightest method first)
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CompressionResult:
    """Result of a compression operation."""
    messages: List[Dict[str, Any]]
    tokens_freed: int
    method: str
    details: Dict[str, Any] = None


class ContextCompressor:
    """
    Five-step context compression manager.
    
    Each layer has different trade-offs:
    - Layer 1: Almost zero loss, zero API cost
    - Layer 2: Low loss, zero API cost
    - Layer 3: Medium loss, zero API cost
    - Layer 4: Medium loss, low API cost
    - Layer 5: High loss, high API cost
    """
    
    # Thresholds
    LARGE_RESULT_THRESHOLD = 50 * 1024  # 50KB
    MAX_MESSAGE_RESULTS = 200 * 1024    # 200KB per message
    CONTEXT_WINDOW_RATIO_1 = 0.90       # 90% - start compressing
    CONTEXT_WINDOW_RATIO_2 = 0.95       # 95% - emergency compress
    MAX_CONTEXT_TOKENS = 180_000        # ~200K window - 20K buffer
    
    def __init__(self, llm_service=None, file_storage_dir: str = "/tmp/memoryai"):
        self.llm = llm_service
        self.file_storage_dir = file_storage_dir

    def maybe_inject_symbolic(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from src.utils.config import settings
        from src.agent.symbolic_memory import inject_symbolic_message

        if not settings.SYMBOLIC_MEMORY_ENABLED:
            return messages
        return inject_symbolic_message(
            messages,
            self.file_storage_dir,
            min_tools=settings.SYMBOLIC_MEMORY_MIN_TOOLS,
        )
    
    async def compress(
        self,
        messages: List[Dict[str, Any]],
        force_level: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Apply compression based on context size.
        
        Args:
            messages: Current message list
            force_level: Force specific compression level (0 = auto)
            
        Returns:
            Compressed message list
        """
        if not messages:
            return messages
        
        # Estimate current token count
        current_tokens = self._estimate_tokens(messages)
        
        # Apply compression layers as needed
        if force_level >= 1 or current_tokens > self.MAX_CONTEXT_TOKENS * 0.5:
            messages = await self._layer1_large_results(messages)
        
        if force_level >= 2 or current_tokens > self.MAX_CONTEXT_TOKENS * 0.7:
            messages = self._layer2_snip_old(messages)
        
        if force_level >= 3 or current_tokens > self.MAX_CONTEXT_TOKENS * 0.8:
            messages = self._layer3_micro_compact(messages)
        
        if force_level >= 4 or current_tokens > self.MAX_CONTEXT_TOKENS * self.CONTEXT_WINDOW_RATIO_1:
            messages = await self._layer4_context_collapse(messages)
        
        if force_level >= 5 or current_tokens > self.MAX_CONTEXT_TOKENS * self.CONTEXT_WINDOW_RATIO_2:
            messages = await self._layer5_full_summary(messages)
        
        return messages
    
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """Estimate token count for messages."""
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        return total_chars // 4  # Rough estimate: 4 chars per token
    
    async def _layer1_large_results(self, messages: List[Dict]) -> List[Dict]:
        """
        Layer 1: Store large tool results to disk.
        
        - Tool results > 50KB stored to disk
        - Keep 2KB preview in message
        - Zero info loss (full content on disk)
        """
        import os
        
        os.makedirs(self.file_storage_dir, exist_ok=True)
        
        modified = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = str(msg.get("content", ""))
                if len(content) > self.LARGE_RESULT_THRESHOLD:
                    # Store to disk
                    import hashlib
                    file_id = hashlib.md5(content.encode()).hexdigest()[:12]
                    file_path = os.path.join(self.file_storage_dir, f"tool_{file_id}.txt")
                    
                    with open(file_path, "w") as f:
                        f.write(content)
                    
                    # Replace with preview
                    preview = content[:2048] + f"\n\n[...完整内容已保存到 {file_path}]"
                    msg = {**msg, "content": preview}
            
            modified.append(msg)
        
        return modified
    
    def _layer2_snip_old(self, messages: List[Dict]) -> List[Dict]:
        """
        Layer 2: Remove old messages from conversation start.
        
        - Remove messages older than threshold
        - Insert boundary marker
        - Low info loss
        """
        if len(messages) <= 10:
            return messages
        
        # Keep last 10 messages, remove older ones
        keep_count = 10
        snip_count = len(messages) - keep_count
        
        if snip_count <= 0:
            return messages
        
        # Insert boundary marker
        boundary = {
            "role": "system",
            "content": f"[...{snip_count} 条更早的消息已被清理...]"
        }
        
        return [boundary] + messages[-keep_count:]
    
    def _layer3_micro_compact(self, messages: List[Dict]) -> List[Dict]:
        """
        Layer 3: Trim old tool outputs.
        
        - Keep recent tool results
        - Clear older tool results
        - Time-based decay
        """
        if len(messages) <= 5:
            return messages
        
        # Keep last 5 tool results, clear others
        tool_count = 0
        modified = []
        
        for msg in messages:
            if msg.get("role") == "tool":
                tool_count += 1
                if tool_count > 5:
                    # Clear old tool result
                    msg = {**msg, "content": "[旧的工具输出已清理]"}
            
            modified.append(msg)
        
        return modified
    
    async def _layer4_context_collapse(self, messages: List[Dict]) -> List[Dict]:
        """
        Layer 4: Context collapse (read-time projection).
        
        - Compress old messages into summary
        - Keep recent messages intact
        - Medium info loss
        """
        if len(messages) <= 15:
            return messages
        
        # Split into old and recent
        old_messages = messages[:-10]
        recent_messages = messages[-10:]
        
        # Summarize old messages
        summary = await self._summarize_messages(old_messages)
        
        # Create collapsed version
        boundary = {
            "role": "system",
            "content": f"[历史摘要]\n{summary}"
        }
        
        return [boundary] + recent_messages
    
    async def _layer5_full_summary(self, messages: List[Dict]) -> List[Dict]:
        """
        Layer 5: Full conversation summary.
        
        - Summarize entire conversation
        - Keep summary only
        - High info loss but preserves key points
        """
        if len(messages) <= 5:
            return messages
        
        summary = await self._summarize_messages(messages)
        
        return [{
            "role": "system",
            "content": f"[完整对话摘要]\n{summary}"
        }]
    
    async def _summarize_messages(self, messages: List[Dict]) -> str:
        """Summarize a list of messages using LLM."""
        if not self.llm:
            # Fallback: simple truncation
            return "\n".join(
                f"{m.get('role', 'unknown')}: {str(m.get('content', ''))[:100]}"
                for m in messages[-5:]
            )
        
        try:
            # Build summarization prompt
            conversation = "\n".join(
                f"{m.get('role', 'unknown')}: {m.get('content', '')}"
                for m in messages
                if m.get("content")
            )
            
            response = await self.llm.generate_response(
                message=f"请用中文总结以下对话的要点：\n\n{conversation[:4000]}",
                system_prompt="你是一个对话总结器。简洁地总结对话要点。"
            )
            
            return response.get("content", "无法生成摘要")
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return "摘要生成失败"
