import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.client = None
        
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self.client = AsyncOpenAI(**kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    async def generate_response(
        self, 
        message: str, 
        context: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> str:
        if not self.client:
            return self._fallback_response(message)
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system", 
                    "content": "你是MemoryAI，一个具备认知记忆架构的智能AI助手。请用中文回答用户的问题，保持简洁和专业。"
                })
            
            if context:
                messages.extend(context)
            
            messages.append({"role": "user", "content": message})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        message_lower = message.lower()
        
        if "你好" in message or "hello" in message_lower or "hi" in message_lower:
            return "你好！我是MemoryAI，很高兴为你服务。请问有什么我可以帮助你的吗？"
        elif "喜欢" in message or "like" in message_lower:
            return "好的，我已经记住了你的偏好！"
        elif "什么" in message or "what" in message_lower:
            return "这是一个很好的问题。让我为你解答。"
        elif "怎么" in message or "how" in message_lower:
            return "让我来帮你解决这个问题。"
        elif "为什么" in message or "why" in message_lower:
            return "这是一个很好的问题。原因如下："
        elif "谢谢" in message or "thank" in message_lower:
            return "不客气！很高兴能帮到你。"
        elif "再见" in message or "bye" in message_lower:
            return "再见！期待下次与你交流。"
        else:
            return f"我收到了你的消息：「{message}」。请问还有什么我可以帮助你的吗？"


llm_service = None


def get_llm_service() -> LLMService:
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
