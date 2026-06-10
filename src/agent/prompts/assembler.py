"""
Dynamic System Prompt Assembler for MemoryAI Agent.

Inspired by Claude Code's architecture:
- Static sections (cached globally)
- Dynamic sections (per-user/per-session)
- Cache boundary marker for cost optimization
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.agent.prompts.sections import (
    PromptSection,
    SectionType,
    CACHE_BOUNDARY_MARKER,
    get_static_prompt,
)

logger = logging.getLogger(__name__)


class PromptAssembler:
    """
    Assembles the System Prompt from multiple sections.
    
    Design principles from Claude Code:
    1. Static content first (cacheable across all users)
    2. Cache boundary marker
    3. Dynamic content after (per-user/per-session)
    4. Memory index always included
    """
    
    def __init__(self):
        self._static_cache: Dict[str, str] = {}
    
    def assemble(
        self,
        environment_info: Dict[str, str] = None,
        memory_index: str = None,
        custom_sections: List[PromptSection] = None,
        scene: str = "general",
    ) -> str:
        """
        Assemble complete System Prompt.
        
        Args:
            environment_info: Current environment (workdir, platform, etc.)
            memory_index: MEMORY.md content (memory index)
            custom_sections: Additional sections to include
            
        Returns:
            Assembled System Prompt string
        """
        parts = []
        
        parts.append(self._get_static_cache(scene))
        
        # 2. Cache boundary
        parts.append(f"\n{'='*50}")
        parts.append(f"{CACHE_BOUNDARY_MARKER}")
        parts.append(f"{'='*50}\n")
        
        # 3. Dynamic sections
        if environment_info:
            parts.append(self._build_environment_section(environment_info))
        
        if memory_index:
            parts.append(self._build_memory_section(memory_index))
        
        if custom_sections:
            for section in custom_sections:
                parts.append(section.content)
        
        return "\n\n".join(parts)
    
    def _get_static_cache(self, scene: str = "general") -> str:
        cache_key = scene or "general"
        if self._static_cache is None:
            self._static_cache = {}
        if cache_key not in self._static_cache:
            self._static_cache[cache_key] = get_static_prompt(cache_key)
        return self._static_cache[cache_key]
    
    def _build_environment_section(self, info: Dict[str, str]) -> str:
        """Build environment information section."""
        lines = ["## 环境信息"]
        
        if "workdir" in info:
            lines.append(f"- 主工作目录: {info['workdir']}")
        if "platform" in info:
            lines.append(f"- 操作系统: {info['platform']}")
        if "session_id" in info:
            lines.append(f"- 会话ID: {info['session_id']}")
        if "timestamp" in info:
            lines.append(f"- 当前时间: {info['timestamp']}")
        
        return "\n".join(lines)
    
    def _build_memory_section(self, memory_index: str) -> str:
        return f"""## 强制记忆（不可忽略）

{memory_index}"""
    
    def invalidate_cache(self):
        self._static_cache = {}


# Global assembler instance
_assembler: Optional[PromptAssembler] = None


def get_prompt_assembler() -> PromptAssembler:
    """Get or create global prompt assembler."""
    global _assembler
    if _assembler is None:
        _assembler = PromptAssembler()
    return _assembler
