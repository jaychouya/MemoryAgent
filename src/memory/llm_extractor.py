import json
import logging
import re
from typing import List, Dict, Any

from src.utils.config import settings

logger = logging.getLogger(__name__)

_EXTRACT_SYSTEM = (
    "你是记忆提取器。从用户与助手的一轮对话中，提取应长期保存的事实（偏好、禁忌、项目决策、外部链接）。"
    "只输出 JSON 数组，每项: {\"content\": \"...\", \"type\": \"user|feedback|project|reference\"}。"
    "无值得记住的内容则输出 []。不要编造。"
)


async def extract_memories_from_turn(
    llm_service,
    user_message: str,
    assistant_message: str,
) -> List[Dict[str, Any]]:
    if not settings.MEMORY_EXTRACT_ENABLED:
        return []
    if not llm_service or not getattr(llm_service, "client", None):
        return []
    text = f"用户: {user_message[:2000]}\n助手: {(assistant_message or '')[:2000]}"
    try:
        resp = await llm_service.generate_response(
            messages=[{"role": "user", "content": text}],
            system_prompt=_EXTRACT_SYSTEM,
        )
        raw = (resp.get("content") if isinstance(resp, dict) else str(resp)) or "[]"
        match = re.search(r"\[[\s\S]*\]", raw)
        if not match:
            return []
        items = json.loads(match.group())
        out = []
        for item in items:
            if not isinstance(item, dict):
                continue
            content = (item.get("content") or "").strip()
            if len(content) < 6:
                continue
            t = (item.get("type") or "user").lower()
            if t not in ("user", "feedback", "project", "reference"):
                t = "user"
            out.append({"content": content, "type": t})
        return out[:5]
    except Exception as e:
        logger.warning(f"LLM memory extract failed: {e}")
        return []
