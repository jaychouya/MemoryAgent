"""Memory aging and verification system."""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryAging:
    """
    Memory aging and verification system.
    
    Inspired by Claude Code:
    - 2 days threshold for stale warning
    - system-reminder wrapper for injection
    - Active verification prompts
    """
    
    # 老化阈值
    STALE_THRESHOLD_DAYS = 2
    
    # 老化警告模板
    STALE_WARNING_TEMPLATE = (
        "这条记忆已经有 {days} 天了。"
        "记忆是某个时间点的观察，不是实时状态——"
        "在当作事实引用之前，请先对照当前代码验证。"
    )
    
    # 主动验证提示
    VERIFICATION_PROMPT = """在基于记忆给出建议之前，请先验证：

1. 如果记忆里写了文件路径，先检查文件是否存在
2. 如果记忆里写了函数名或 flag，先 grep 一下
3. 如果用户要照你的建议动手了，先验证再说

「记忆说 X 存在」不等于「X 现在存在」"""
    
    def __init__(self):
        pass
    
    def calculate_age(self, memory: Dict[str, Any]) -> Optional[int]:
        """Calculate age of memory in days."""
        created_at = memory.get("created_at")
        
        if not created_at:
            return None
        
        try:
            if isinstance(created_at, str):
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created = created_at
            
            return (datetime.now() - created.replace(tzinfo=None)).days
        except:
            return None
    
    def is_stale(self, memory: Dict[str, Any]) -> bool:
        """Check if memory is stale."""
        age_days = self.calculate_age(memory)
        
        if age_days is None:
            return False
        
        return age_days >= self.STALE_THRESHOLD_DAYS
    
    def get_stale_warning(self, memory: Dict[str, Any]) -> Optional[str]:
        """Get staleness warning for memory."""
        age_days = self.calculate_age(memory)
        
        if age_days is None:
            return None
        
        if age_days >= self.STALE_THRESHOLD_DAYS:
            return self.STALE_WARNING_TEMPLATE.format(days=age_days)
        
        return None
    
    def wrap_with_system_reminder(
        self,
        memory: Dict[str, Any],
        content: str
    ) -> str:
        """
        Wrap memory content with system-reminder tags.
        
        Inspired by Claude Code's injection format:
        <system-reminder>
        This memory was saved 5 days ago. Verify it's still accurate.
        
        [memory content]
        </system-reminder>
        """
        age_days = self.calculate_age(memory)
        
        if age_days is not None and age_days >= self.STALE_THRESHOLD_DAYS:
            warning = f"This memory was saved {age_days} days ago. Verify it's still accurate before acting on it."
        else:
            warning = None
        
        # 构建 system-reminder
        parts = ["<system-reminder>"]
        
        if warning:
            parts.append(warning)
            parts.append("")
        
        parts.append(content)
        parts.append("</system-reminder>")
        
        return "\n".join(parts)
    
    def get_verification_prompt(self) -> str:
        """Get verification prompt."""
        return self.VERIFICATION_PROMPT
    
    def inject_memories(
        self,
        memories: List[Dict[str, Any]]
    ) -> str:
        """
        Inject memories with aging warnings.
        
        Returns formatted text for system prompt.
        """
        if not memories:
            return ""
        
        parts = ["## 相关记忆\n"]
        
        for memory in memories:
            content = memory.get("content", "")
            description = memory.get("description", "")
            memory_type = memory.get("type", "unknown")
            
            # 构建记忆文本
            memory_text = f"### {description}\n"
            memory_text += f"类型: {memory_type}\n\n"
            memory_text += content
            
            # 添加老化警告
            stale_warning = memory.get("stale_warning")
            if stale_warning:
                memory_text += f"\n\n⚠️ {stale_warning}"
            
            # 包装为 system-reminder
            wrapped = self.wrap_with_system_reminder(memory, memory_text)
            parts.append(wrapped)
            parts.append("")
        
        # 如果有旧记忆，添加验证提示
        has_stale = any(self.is_stale(m) for m in memories)
        if has_stale:
            parts.append("---")
            parts.append(self.VERIFICATION_PROMPT)
        
        return "\n".join(parts)
    
    def get_stats(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get aging statistics."""
        total = len(memories)
        stale = sum(1 for m in memories if self.is_stale(m))
        
        ages = []
        for memory in memories:
            age = self.calculate_age(memory)
            if age is not None:
                ages.append(age)
        
        avg_age = sum(ages) / len(ages) if ages else None
        
        return {
            "total_memories": total,
            "stale_memories": stale,
            "stale_percentage": (stale / total * 100) if total > 0 else 0,
            "average_age_days": avg_age,
            "stale_threshold_days": self.STALE_THRESHOLD_DAYS
        }
