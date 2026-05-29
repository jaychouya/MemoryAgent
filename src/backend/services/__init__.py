import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize LLM service.
        
        Args:
            api_key: OpenAI API key (optional, can use env var)
            model: Model to use for generation
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate_response(
        self, 
        message: str, 
        context: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            message: User message
            context: Previous conversation context
            system_prompt: System prompt for the model
            
        Returns:
            Generated response text
        """
        try:
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({
                    "role": "system", 
                    "content": """你是MemoryAI，一个具备认知记忆架构的智能AI助手。
你的特点：
1. 能够记住用户的偏好和习惯
2. 提供个性化的回答
3. 友好、专业、有帮助

请用中文回答用户的问题，保持简洁和专业。"""
                })
            
            # Add context if provided
            if context:
                messages.extend(context)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Call LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            # Fallback to simple response if LLM fails
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Generate a simple fallback response when LLM is unavailable."""
        if "你好" in message or "hello" in message.lower():
            return "你好！我是MemoryAI，很高兴为你服务。"
        elif "喜欢" in message or "like" in message.lower():
            return "好的，我已经记住了你的偏好！"
        elif "什么" in message or "what" in message.lower():
            return "这是一个很好的问题。让我为你解答。"
        else:
            return "我收到了你的消息。请问还有什么我可以帮助你的吗？"


# Global LLM service instance
llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global llm_service
    if llm_service is None:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        llm_service = LLMService(api_key=api_key)
    return llm_service
