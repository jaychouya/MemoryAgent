"""
Built-in tools for MemoryAI Agent.

These tools provide core functionality:
- Memory search
- Memory store
- Context retrieval
"""

import html
import re
from typing import Any, Dict, List
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse

import httpx

from src.agent.tools.base import ReadOnlyTool, ReadWriteTool, ToolResult


class MemorySearchTool(ReadOnlyTool):
    """Search through memory system."""
    
    name = "memory_search"
    description = "搜索记忆系统，查找相关信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或问题"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
    async def execute(self, query: str, top_k: int = 5, **kwargs) -> ToolResult:
        """Search memories."""
        try:
            from src.utils import as_int

            top_k = as_int(top_k, 5)
            user_id = kwargs.get("user_id", "anonymous")
            
            results = await self.memory.retrieve(
                user_id=user_id,
                query=query,
                top_k=top_k
            )
            
            if not results:
                return ToolResult(
                    success=True,
                    content="暂无相关记忆。这是新对话，请直接回答用户的问题。"
                )
            
            # Format results
            content = "找到以下相关记忆：\n\n"
            for i, result in enumerate(results[:top_k], 1):
                # result 是 dict，包含 content, score 等字段
                memory_content = result.get("content", "无内容")
                score = result.get("score", 0)
                content += f"{i}. {memory_content}\n"
                content += f"   (相关度: {score:.2f})\n\n"
            
            return ToolResult(
                success=True,
                content=content,
                metadata={"count": len(results)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"记忆搜索失败: {str(e)}"
            )


class MemoryStoreTool(ReadWriteTool):
    """Store information to memory."""
    
    name = "memory_store"
    description = "存储信息到记忆系统"
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要存储的内容"
            },
            "memory_type": {
                "type": "string",
                "enum": ["user", "feedback", "project", "reference"],
                "description": "记忆类型"
            },
            "importance": {
                "type": "number",
                "description": "重要性分数 (0-1)",
                "default": 0.5
            }
        },
        "required": ["content", "memory_type"]
    }
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
    
    async def execute(
        self,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        **kwargs
    ) -> ToolResult:
        """Store memory."""
        try:
            from src.memory.types import MemoryType
            
            type_map = {
                "user": MemoryType.USER,
                "feedback": MemoryType.FEEDBACK,
                "project": MemoryType.PROJECT,
                "reference": MemoryType.REFERENCE
            }
            
            mem_type = type_map.get(memory_type, MemoryType.USER)
            
            # 生成有意义的描述
            description = self._generate_description(content, memory_type)
            
            # 获取用户上下文
            user_id = kwargs.get("user_id", "anonymous")
            session_id = kwargs.get("session_id")
            
            # 构建元数据
            metadata = {
                "user_id": user_id,
                "importance": importance,
                "source": "user_conversation"
            }
            if session_id:
                metadata["session_id"] = session_id
            
            result = await self.memory.store(
                content=content,
                memory_type=mem_type,
                description=description,
                metadata=metadata,
                user_id=user_id
            )
            
            if result:
                return ToolResult(
                    success=True,
                    content=f"已成功存储记忆到 {memory_type} 类型\n\n存储内容: {content[:100]}"
                )
            else:
                return ToolResult(
                    success=False,
                    content=None,
                    error="记忆存储失败"
                )
            
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"记忆存储失败: {str(e)}"
            )
    
    def _generate_description(self, content: str, memory_type: str) -> str:
        """Generate a meaningful description for the memory."""
        # 截取前30个字符作为基础
        base = content[:30] if len(content) > 30 else content
        
        # 根据类型添加前缀
        type_prefixes = {
            "user": "用户偏好",
            "feedback": "行为反馈",
            "project": "项目动态",
            "reference": "外部引用"
        }
        
        prefix = type_prefixes.get(memory_type, "记忆")
        return f"{prefix}：{base}"


class ContextRetrieveTool(ReadOnlyTool):
    """Retrieve conversation context."""
    
    name = "context_retrieve"
    description = "获取当前对话上下文"
    parameters = {
        "type": "object",
        "properties": {
            "last_n": {
                "type": "integer",
                "description": "获取最近N条消息",
                "default": 5
            }
        }
    }
    
    async def execute(self, last_n: int = 5, **kwargs) -> ToolResult:
        """Get conversation context."""
        from src.utils import as_int

        last_n = as_int(last_n, 5)
        messages = kwargs.get("messages", [])
        
        recent = messages[-last_n:] if messages else []
        
        if not recent:
            return ToolResult(
                success=True,
                content="暂无对话历史。"
            )
        
        content = "最近的对话：\n\n"
        for msg in recent:
            role = "用户" if msg.get("role") == "user" else "助手"
            content += f"**{role}**: {msg.get('content', '')[:100]}...\n\n"
        
        return ToolResult(
            success=True,
            content=content
        )


class WebSearchTool(ReadOnlyTool):
    """Search public web pages."""

    name = "web_search"
    description = "联网搜索公开网页，适合查询真题、新闻、文档等实时或外部信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词或问题"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, top_k: int = 5, **kwargs) -> ToolResult:
        try:
            from src.utils import as_int

            top_k = as_int(top_k, 5)
            url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                response.raise_for_status()

            results = self._parse_results(response.text, top_k)
            if not results:
                return ToolResult(success=True, content="未找到可用的联网搜索结果。")

            content = "联网搜索结果：\n\n"
            for i, item in enumerate(results, 1):
                content += f"{i}. {item['title']}\n"
                content += f"   {item['url']}\n"
                if item.get("snippet"):
                    content += f"   {item['snippet']}\n"
                content += "\n"
            return ToolResult(
                success=True,
                content=content,
                metadata={"count": len(results), "query": query}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"联网搜索失败: {str(e)}"
            )

    def _parse_results(self, body: str, top_k: int) -> List[Dict[str, str]]:
        results = []
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S)
        for href, title in links:
            title = re.sub(r"<[^>]+>", "", title)
            title = html.unescape(title).strip()
            if not title:
                continue

            url = html.unescape(href)
            parsed = urlparse(url)
            if parsed.path.startswith("/l/"):
                uddg = parse_qs(parsed.query).get("uddg", [""])[0]
                if uddg:
                    url = unquote(uddg)
            if not url.startswith(("http://", "https://")):
                continue

            results.append({"title": title, "url": url, "snippet": ""})
            if len(results) >= top_k:
                break
        return results


class WebFetchTool(ReadOnlyTool):
    """Fetch a public web page."""

    name = "web_fetch"
    description = "抓取公开网页内容，适合读取指定 URL 的网页正文"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要抓取的公开网页 URL"
            },
            "extractMode": {
                "type": "string",
                "enum": ["markdown", "text"],
                "description": "提取模式",
                "default": "markdown"
            },
            "maxChars": {
                "type": "integer",
                "description": "最多返回字符数",
                "default": 10000
            },
            "search_query": {
                "type": "string",
                "description": "抓取失败时用于联网搜索的备用关键词（建议填用户原问题）"
            }
        },
        "required": ["url"]
    }

    async def execute(
        self,
        url: str,
        extractMode: str = "markdown",
        maxChars: int = 10000,
        search_query: str = "",
        **kwargs
    ) -> ToolResult:
        try:
            from src.utils import as_int

            max_chars = as_int(maxChars, 10000)
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return ToolResult(
                    success=False,
                    content=None,
                    error="只支持 http/https URL"
                )

            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    }
                )
                if response.status_code == 403:
                    return await self._blocked_result(url, max_chars, search_query)
                response.raise_for_status()

            text = self._extract_text(response.text, url)
            from src.agent.tool_result_format import _filter_noise_lines

            text = _filter_noise_lines(text, max_lines=30)
            if max_chars > 0:
                text = text[:max_chars]
            return ToolResult(
                success=True,
                content=f"网页内容：\n\n{text}",
                metadata={"url": url, "extractMode": extractMode}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content=None,
                error=f"网页抓取失败: {str(e)}"
            )

    async def _blocked_result(
        self, url: str, max_chars: int, search_query: str = ""
    ) -> ToolResult:
        from src.agent.tool_result_format import guess_search_query

        query = guess_search_query(url, search_query)
        search = await WebSearchTool().execute(query, top_k=5)
        content = (
            f"目标网页返回 403 Forbidden（{url}），无法直接抓取。\n\n"
            f"已用关键词「{query}」联网搜索替代来源：\n\n"
        )
        if search.success and search.content:
            content += search.content
        else:
            content += "联网搜索也没有找到可用结果。"
        if max_chars > 0:
            content = content[:max_chars]
        return ToolResult(
            success=True,
            content=content,
            metadata={"url": url, "status_code": 403, "fallback": "web_search"},
        )

    def _extract_text(self, body: str, base_url: str = "") -> str:
        article = self._extract_article(body)
        if article:
            body = article
        image_lines = self._extract_images(body, base_url)
        body = re.sub(r"(?is)<script.*?</script>", " ", body)
        body = re.sub(r"(?is)<style.*?</style>", " ", body)
        body = re.sub(r"(?is)<img[^>]+>", " ", body)
        body = re.sub(r"(?i)<br\s*/?>", "\n", body)
        body = re.sub(r"(?i)</p\s*>", "\n\n", body)
        body = re.sub(r"(?i)</h[1-6]\s*>", "\n\n", body)
        body = re.sub(r"<[^>]+>", " ", body)
        body = html.unescape(body)
        body = re.sub(r"[ \t\r\f\v]+", " ", body)
        body = re.sub(r"\n\s+", "\n", body)
        body = re.sub(r"\n{3,}", "\n\n", body)
        text = body.strip()
        if image_lines:
            text = (
                f"{text}\n\n"
                "注意：该网页的主要正文以图片形式发布；当前已成功抓取网页，"
                "但没有 OCR 引擎，不能直接把图片中的题目转成文本。"
                "请不要说网页访问受限，可以把以下图片链接提供给用户，"
                "或请用户发送具体题目图片/文字后再讲解。\n\n"
                "页面图片：\n"
                + "\n".join(image_lines)
            )
        return text.strip()

    def _extract_article(self, body: str) -> str:
        match = re.search(
            r'<div[^>]+class=["\']?TRS_Editor["\']?[^>]*>(.*?)</div>',
            body,
            re.S,
        )
        if match:
            return match.group(1)
        match = re.search(
            r'<article[^>]*>(.*?)</article>',
            body,
            re.S | re.I,
        )
        return match.group(1) if match else ""

    def _extract_images(self, body: str, base_url: str) -> List[str]:
        images = []
        for tag in re.findall(r"(?is)<img[^>]+>", body):
            src_match = re.search(r'''src=["']([^"']+)["']''', tag, re.I)
            if not src_match:
                continue
            alt_match = re.search(r'''alt=["']([^"']*)["']''', tag, re.I)
            src = urljoin(base_url, html.unescape(src_match.group(1)).strip())
            if src.startswith("data:"):
                continue
            low = src.lower()
            if any(x in low for x in ("logo", "icon", "share.png", "avatar", "qrcode")):
                continue
            alt = html.unescape(alt_match.group(1)).strip() if alt_match else ""
            label = f"{alt}: {src}" if alt else src
            if label not in images:
                images.append(label)
            if len(images) >= 8:
                break
        return images


# Export all built-in tools
BUILTIN_TOOLS = [
    MemorySearchTool,
    MemoryStoreTool,
    ContextRetrieveTool,
    WebSearchTool,
    WebFetchTool,
]
