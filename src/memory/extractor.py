"""Extract Memories Agent - independent agent for memory extraction."""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMemory:
    """A memory extracted from conversation."""
    content: str
    memory_type: str  # user, feedback, project, reference
    description: str
    reason: str  # Why this is worth remembering
    confidence: float  # 0-1


class ExtractMemoriesAgent:
    """
    Independent agent for extracting memories from conversations.
    
    Inspired by Claude Code's extractMemories agent:
    - Forked from main conversation (shares prompt cache)
    - Runs after each turn completes
    - Only extracts structured memories
    - Checks for duplicates before writing
    """
    
    # 记忆类型定义
    MEMORY_TYPES = {
        "user": {
            "label": "用户画像",
            "description": "用户的身份、角色、知识水平",
            "examples": ["十年 Go 后端", "刚接触 React"]
        },
        "feedback": {
            "label": "行为偏好",
            "description": "用户喜欢/不喜欢什么，确认有效的做法",
            "examples": ["不要用 mock 数据库", "diff 就够了不要总结"]
        },
        "project": {
            "label": "项目动态",
            "description": "项目正在发生什么，截止日期，重要决策",
            "examples": ["3月5号开始合并冻结", "API gateway 用的是 Kong"]
        },
        "reference": {
            "label": "外部指针",
            "description": "去哪查什么信息",
            "examples": ["pipeline bug 在 Linear 的 INGEST 项目", "Grafana 看板地址"]
        }
    }
    
    # 排除规则：不该存什么
    EXCLUSION_RULES = [
        "代码模式、架构、文件路径、项目结构（用 grep 就能得到）",
        "Git 历史和最近改动（git log 是权威）",
        "调试方案和修复方法（fix 已经在代码里）",
        "CLAUDE.md 里已经写过的内容",
        "临时任务状态和当前对话上下文"
    ]
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
        self.extracted_count = 0
    
    async def extract(
        self,
        messages: List[Dict[str, Any]],
        existing_memories: List[Dict[str, Any]] = None
    ) -> List[ExtractedMemory]:
        """
        Extract memories from conversation messages.
        
        Args:
            messages: Conversation messages
            existing_memories: Existing memories to check for duplicates
            
        Returns:
            List of extracted memories
        """
        if not self.llm:
            logger.warning("No LLM service available for memory extraction")
            return []
        
        # 构建提取提示词
        prompt = self._build_extraction_prompt(messages, existing_memories or [])
        
        try:
            # 调用 LLM 提取记忆
            response = await self.llm.generate_response(
                message=prompt,
                system_prompt=self._get_system_prompt()
            )
            
            # 解析结果
            content = response.get("content", "")
            memories = self._parse_extracted_memories(content)
            
            # 过滤重复
            memories = self._filter_duplicates(memories, existing_memories or [])
            
            self.extracted_count += len(memories)
            
            if memories:
                logger.info(f"Extracted {len(memories)} new memories")
            
            return memories
            
        except Exception as e:
            logger.error(f"Memory extraction failed: {e}")
            return []
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for extraction agent."""
        return """你是一个记忆抽取代理。你的任务是从对话中提取值得记住的信息。

规则：
1. 只提取用户明确表达的偏好、反馈、项目信息、外部引用
2. 不要提取代码模式、文件路径、Git 历史等可以通过工具获取的信息
3. 不要提取临时任务状态
4. 每条记忆必须包含：内容、类型、描述、原因

记忆类型：
- user: 用户画像（身份、角色、知识水平）
- feedback: 行为偏好（喜欢/不喜欢什么，有效做法）
- project: 项目动态（截止日期、重要决策）
- reference: 外部指针（去哪查什么）

输出格式（JSON 数组）：
```json
[
  {
    "content": "记忆内容",
    "memory_type": "user|feedback|project|reference",
    "description": "一句话描述",
    "reason": "为什么值得记住",
    "confidence": 0.8
  }
]
```

如果没有值得记住的信息，返回空数组 `[]`。"""
    
    def _build_extraction_prompt(
        self,
        messages: List[Dict[str, Any]],
        existing_memories: List[Dict[str, Any]]
    ) -> str:
        """Build extraction prompt."""
        # 构建对话历史
        conversation = []
        for msg in messages[-10:]:  # 只取最近10条
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                conversation.append(f"{role}: {content[:200]}")
        
        conversation_text = "\n".join(conversation)
        
        # 构建现有记忆摘要
        existing_summary = ""
        if existing_memories:
            existing_summary = "\n\n现有记忆（避免重复）：\n"
            for mem in existing_memories[:20]:
                existing_summary += f"- {mem.get('description', '')}\n"
        
        return f"""请从以下对话中提取值得记住的信息：

对话历史：
{conversation_text}
{existing_summary}

请提取新的、有价值的记忆。返回 JSON 数组。"""
    
    def _parse_extracted_memories(self, content: str) -> List[ExtractedMemory]:
        """Parse extracted memories from LLM response."""
        try:
            # 尝试提取 JSON
            json_start = content.find("[")
            json_end = content.rfind("]") + 1
            
            if json_start == -1 or json_end == 0:
                return []
            
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            memories = []
            for item in data:
                if isinstance(item, dict):
                    memory = ExtractedMemory(
                        content=item.get("content", ""),
                        memory_type=item.get("memory_type", "user"),
                        description=item.get("description", "")[:100],
                        reason=item.get("reason", ""),
                        confidence=min(1.0, max(0.0, item.get("confidence", 0.5)))
                    )
                    
                    # 验证类型
                    if memory.memory_type in self.MEMORY_TYPES:
                        memories.append(memory)
            
            return memories
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse extracted memories: {e}")
            return []
    
    def _filter_duplicates(
        self,
        new_memories: List[ExtractedMemory],
        existing_memories: List[Dict[str, Any]]
    ) -> List[ExtractedMemory]:
        """Filter out duplicate memories."""
        if not existing_memories:
            return new_memories
        
        # 构建现有记忆的描述集合
        existing_descriptions = set()
        for mem in existing_memories:
            desc = mem.get("description", "").lower().strip()
            if desc:
                existing_descriptions.add(desc)
        
        # 过滤重复
        filtered = []
        for memory in new_memories:
            desc = memory.description.lower().strip()
            
            # 检查是否重复
            is_duplicate = False
            for existing_desc in existing_descriptions:
                # 简单的相似度检查
                if self._is_similar(desc, existing_desc):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(memory)
        
        return filtered
    
    def _is_similar(self, text1: str, text2: str, threshold: float = 0.5) -> bool:
        """Check if two texts are similar."""
        if not text1 or not text2:
            return False
        
        # 中文按字符分词，英文按空格分词
        import re
        def tokenize(text):
            # 提取中文字符和英文单词
            chinese = re.findall(r'[\u4e00-\u9fff]', text)
            english = re.findall(r'[a-zA-Z]+', text)
            return set(chinese + english)
        
        words1 = tokenize(text1)
        words2 = tokenize(text2)
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return {
            "extracted_count": self.extracted_count,
            "memory_types": list(self.MEMORY_TYPES.keys()),
            "exclusion_rules": len(self.EXCLUSION_RULES)
        }
