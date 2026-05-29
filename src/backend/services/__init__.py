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
            return "你好！我是MemoryAI，一个具备认知记忆架构的智能AI助手。\n\n我可以帮你：\n• 回答各种问题\n• 记住你的偏好和习惯\n• 提供个性化的建议\n\n请问有什么我可以帮助你的吗？"
        elif "喜欢" in message or "like" in message_lower:
            return f"好的，我记住了！{message}\n\n我会把这个偏好保存到记忆中，下次会参考这个信息来更好地为你服务。"
        elif "什么" in message:
            return f"关于你问的「{message}」，这是一个很好的问题。\n\n不过目前我还没有配置AI模型，无法提供详细的回答。请点击左上角的「配置」按钮，选择一个AI厂商并填写API Key，我就能给你更智能的回答了。\n\n配置完成后，我可以：\n• 详细解答你的问题\n• 提供相关的背景知识\n• 给出实用的建议"
        elif "怎么" in message or "如何" in message:
            return f"关于「{message}」，我来帮你分析一下。\n\n目前我处于基础模式，回答能力有限。如需更详细的指导，请配置AI模型：\n1. 点击左上角「配置」按钮\n2. 选择AI厂商（如百炼、OpenAI等）\n3. 填写API Key\n4. 保存配置\n\n配置完成后，我就能给你更专业的解答了！"
        elif "为什么" in message:
            return f"你问的「{message}」很有深度！\n\n要回答这个问题，需要更强大的AI能力。目前我处于基础模式，建议你配置AI模型以获得更准确的分析和解答。\n\n配置方法：点击左上角「配置」按钮，选择厂商并填写API Key即可。"
        elif "谢谢" in message or "thank" in message_lower:
            return "不客气！很高兴能帮到你。😊\n\n如果还有其他问题，随时可以问我。"
        elif "再见" in message or "bye" in message_lower:
            return "再见！期待下次与你交流。👋\n\n我会记住我们的对话，下次见面时可以继续。"
        elif "你是谁" in message or "介绍" in message:
            return "我是MemoryAI，一个基于认知记忆架构的智能AI助手。\n\n🧠 **我的特点：**\n• **四层记忆系统**：工作记忆、短期记忆、长期记忆、情景记忆\n• **跨会话记忆**：记住你的偏好和历史\n• **智能决策**：自主判断何时需要确认\n• **可解释性**：告诉你我为什么这样回答\n\n目前处于基础模式，配置AI模型后可以发挥全部能力！"
        else:
            return f"收到你的消息：「{message}」\n\n目前我处于基础模式，回答能力有限。如需更智能的回答，请配置AI模型：\n\n👉 点击左上角「配置」按钮\n👉 选择AI厂商\n👉 填写API Key\n\n配置后我就能真正理解你的问题并给出有用的回答了！"


llm_service = None


def get_llm_service() -> LLMService:
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
