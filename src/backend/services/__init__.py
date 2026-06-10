import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
import os
import re
import uuid

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
                kwargs = {"api_key": self.api_key, "timeout": 90.0}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self.client = AsyncOpenAI(**kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    async def generate_response(
        self, 
        message: str = None,
        messages: List[Dict[str, str]] = None,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        tools: List[Dict] = None
    ) -> Dict[str, Any]:
        if not self.client:
            msg = self._extract_user_message(message, messages)
            return {
                "content": self._fallback_response(msg, is_configured=False),
                "stop_reason": "end_turn"
            }
        
        try:
            api_messages = []
            
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            else:
                api_messages.append({
                    "role": "system", 
                    "content": """你是 MemoryAgent，带长期记忆的通用 AI 助手（不限于考研或刷题）。请遵循以下回答规范：

## 回答规范

1. **结构清晰**：使用标题、列表、代码块等格式组织内容
2. **简洁专业**：直接回答问题，避免冗余废话
3. **中文优先**：默认使用中文回答，除非用户使用英文提问

请根据用户问题，提供专业、结构化的回答。"""
                })
            
            if messages:
                api_messages.extend(messages)
            elif context:
                api_messages.extend(context)
                api_messages.append({"role": "user", "content": message})
            else:
                api_messages.append({"role": "user", "content": message})
            
            kwargs = {
                "model": self.model,
                "messages": api_messages,
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # 后处理：清理 Markdown 格式
            content = self._clean_markdown(content)
            
            result = {
                "content": content,
                "stop_reason": choice.finish_reason
            }
            
            if choice.message.tool_calls:
                result["tool_calls"] = []
                for tc in choice.message.tool_calls:
                    result["tool_calls"].append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    })
            elif tools:
                xml_tool_call = self._parse_xml_tool_call(content)
                if xml_tool_call:
                    result["content"] = ""
                    result["tool_calls"] = [xml_tool_call]
            
            return result

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            error_msg = str(e)
            user_msg = self._extract_user_message(message, messages)
            if "401" in error_msg or "api_key" in error_msg.lower():
                err = "API Key 无效，请检查并重新配置。"
            elif "429" in error_msg:
                err = "请求过于频繁，请稍后再试。"
            elif "Connection error" in error_msg or "connect" in error_msg.lower():
                err = f"无法连接到AI服务 ({self.base_url})，请检查API地址是否正确。"
            elif "404" in error_msg:
                err = f"模型 '{self.model}' 不存在，请检查模型名称是否正确。"
            else:
                err = f"AI服务出错: {error_msg[:100]}"
            return {
                "content": self._fallback_response(user_msg, is_configured=True, error=err),
                "stop_reason": "end_turn",
            }

    async def generate_response_stream(
        self,
        message: str = None,
        messages: List[Dict[str, str]] = None,
        context: List[Dict[str, str]] = None,
        system_prompt: str = None,
        tools: List[Dict] = None,
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> Dict[str, Any]:
        if tools:
            return await self.generate_response(
                message=message,
                messages=messages,
                context=context,
                system_prompt=system_prompt,
                tools=tools,
            )
        if not self.client:
            msg = self._extract_user_message(message, messages)
            content = self._fallback_response(msg, is_configured=False)
            if on_token:
                for ch in content:
                    await on_token(ch)
            return {"content": content, "stop_reason": "end_turn", "streamed": True}

        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        else:
            api_messages.append({
                "role": "system",
                "content": "你是MemoryAI，一个专业的AI助手。请用中文简洁回答。",
            })
        if messages:
            api_messages.extend(messages)
        elif context:
            api_messages.extend(context)
            api_messages.append({"role": "user", "content": message})
        else:
            api_messages.append({"role": "user", "content": message})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=0.7,
                max_tokens=4000,
                stream=True,
            )
            parts: List[str] = []
            finish_reason = "end_turn"
            async for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                delta = choice.delta.content or ""
                if delta:
                    parts.append(delta)
                    if on_token:
                        await on_token(delta)
            raw = "".join(parts)
            content = self._clean_markdown(raw) if raw.strip() else ""
            if not content.strip():
                user_msg = self._extract_user_message(message, messages)
                content = self._fallback_response(
                    user_msg,
                    is_configured=bool(self.client),
                    error="模型返回为空，请重试或检查模型配置。",
                )
                if on_token and not parts:
                    for ch in content:
                        await on_token(ch)
            return {
                "content": content,
                "stop_reason": finish_reason,
                "streamed": True,
            }
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            error_msg = str(e)
            user_msg = self._extract_user_message(message, messages)
            if "401" in error_msg or "api_key" in error_msg.lower():
                err = "API Key 无效，请检查并重新配置。"
            elif "429" in error_msg:
                err = "请求过于频繁，请稍后再试。"
            elif "Connection error" in error_msg or "connect" in error_msg.lower():
                err = f"无法连接到AI服务 ({self.base_url})，请检查API地址是否正确。"
            elif "404" in error_msg:
                err = f"模型 '{self.model}' 不存在，请检查模型名称是否正确。"
            else:
                err = f"AI服务出错: {error_msg[:100]}"
            content = self._fallback_response(user_msg, is_configured=True, error=err)
            if on_token:
                for ch in content:
                    await on_token(ch)
            return {"content": content, "stop_reason": "end_turn", "streamed": True}

    def _parse_xml_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        if not content or "<tool_call>" not in content:
            return None
        func_match = re.search(
            r"<function=([a-zA-Z0-9_]+)>(.*?)</function>",
            content,
            re.S,
        )
        if not func_match:
            return None

        name = func_match.group(1)
        body = func_match.group(2)
        params: Dict[str, Any] = {}
        for key, value in re.findall(
            r"<parameter=([a-zA-Z0-9_]+)>(.*?)</parameter>",
            body,
            re.S,
        ):
            value = value.strip()
            if value.isdigit():
                params[key] = int(value)
            else:
                params[key] = value

        import json

        return {
            "id": f"call_{uuid.uuid4().hex[:12]}",
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(params, ensure_ascii=False),
            },
        }
    
    def _extract_user_message(
        self,
        message: Optional[str],
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        if message:
            return message
        if messages:
            for m in reversed(messages):
                if m.get("role") == "user":
                    return m.get("content", "") or ""
        return ""

    def _fallback_response(self, message: str, is_configured: bool = False, error: str = None) -> str:
        message = message or ""
        if error and is_configured:
            label = f"「{message}」" if message else "你的问题"
            return (
                f"关于{label}，调用模型时出错。\n\n"
                f"⚠️ {error}\n\n"
                "请检查左上角「配置」中的 API Key、Base URL 和模型名称。"
            )
        message_lower = message.lower()
        
        if "你好" in message or "hello" in message_lower or "hi" in message_lower:
            return "你好！我是MemoryAI，一个具备认知记忆架构的智能AI助手。\n\n我可以帮你：\n• 回答各种问题\n• 记住你的偏好和习惯\n• 提供个性化的建议\n\n请问有什么我可以帮助你的吗？"
        elif "喜欢" in message or "like" in message_lower:
            return f"好的，我记住了！{message}\n\n我会把这个偏好保存到记忆中，下次会参考这个信息来更好地为你服务。"
        elif "什么" in message:
            if is_configured:
                return f"关于你问的「{message}」，这是一个很好的问题。\n\n⚠️ {error}\n\n请检查你的API配置是否正确：\n1. 点击左上角「配置」按钮\n2. 确认API Key是否有效\n3. 确认选择的厂商和模型是否正确\n\n如需帮助，可以参考厂商文档获取正确的API Key。"
            else:
                return f"关于你问的「{message}」，这是一个很好的问题。\n\n不过目前我还没有配置AI模型，无法提供详细的回答。请点击左上角的「配置」按钮，选择一个AI厂商并填写API Key，我就能给你更智能的回答了。\n\n配置完成后，我可以：\n• 详细解答你的问题\n• 提供相关的背景知识\n• 给出实用的建议"
        elif "怎么" in message or "如何" in message:
            if is_configured:
                return f"关于「{message}」，我来帮你分析一下。\n\n⚠️ {error}\n\n请检查你的API配置是否正确：\n1. 点击左上角「配置」按钮\n2. 确认API Key是否有效\n3. 确认选择的厂商和模型是否正确\n\n如需帮助，可以参考厂商文档获取正确的API Key。"
            else:
                return f"关于「{message}」，我来帮你分析一下。\n\n目前我处于基础模式，回答能力有限。如需更详细的指导，请配置AI模型：\n1. 点击左上角「配置」按钮\n2. 选择AI厂商（如百炼、OpenAI等）\n3. 填写API Key\n4. 保存配置\n\n配置完成后，我就能给你更专业的解答了！"
        elif "为什么" in message:
            if is_configured:
                return f"你问的「{message}」很有深度！\n\n⚠️ {error}\n\n请检查你的API配置是否正确：\n1. 点击左上角「配置」按钮\n2. 确认API Key是否有效\n3. 确认选择的厂商和模型是否正确\n\n如需帮助，可以参考厂商文档获取正确的API Key。"
            else:
                return f"你问的「{message}」很有深度！\n\n要回答这个问题，需要更强大的AI能力。目前我处于基础模式，建议你配置AI模型以获得更准确的分析和解答。\n\n配置方法：点击左上角「配置」按钮，选择厂商并填写API Key即可。"
        elif "谢谢" in message or "thank" in message_lower:
            return "不客气！很高兴能帮到你。😊\n\n如果还有其他问题，随时可以问我。"
        elif "再见" in message or "bye" in message_lower:
            return "再见！期待下次与你交流。👋\n\n我会记住我们的对话，下次见面时可以继续。"
        elif "你是谁" in message or "介绍" in message:
            return "我是MemoryAI，一个基于认知记忆架构的智能AI助手。\n\n🧠 **我的特点：**\n• **四层记忆系统**：工作记忆、短期记忆、长期记忆、情景记忆\n• **跨会话记忆**：记住你的偏好和历史\n• **智能决策**：自主判断何时需要确认\n• **可解释性**：告诉你我为什么这样回答\n\n目前处于基础模式，配置AI模型后可以发挥全部能力！"
        else:
            if is_configured:
                return f"收到你的消息：「{message}」\n\n⚠️ {error}\n\n请检查你的API配置是否正确：\n1. 点击左上角「配置」按钮\n2. 确认API Key是否有效\n3. 确认选择的厂商和模型是否正确\n\n如需帮助，可以参考厂商文档获取正确的API Key。"
            else:
                return f"收到你的消息：「{message}」\n\n目前我处于基础模式，回答能力有限。如需更智能的回答，请配置AI模型：\n\n👉 点击左上角「配置」按钮\n👉 选择AI厂商\n👉 填写API Key\n\n配置后我就能真正理解你的问题并给出有用的回答了！"
    
    def _clean_markdown(self, text: str) -> str:
        """移除工具 XML 泄漏，规范化数学 Markdown 供前端渲染。"""
        from src.agent.output_format import normalize_agent_output
        return normalize_agent_output(text)


llm_service = None


def get_llm_service() -> LLMService:
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
