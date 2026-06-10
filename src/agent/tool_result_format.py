"""Format raw tool output into user-friendly replies."""

import re
from typing import List, Optional
from urllib.parse import unquote, urlparse

_NAV_LINE = re.compile(
    r"^(首页|考研|登录|退出|更多|关于|版权|分享|复制链接|热门推荐|相关文章|"
    r"经营许可证|Copyright|All Rights Reserved|微博|知乎|哔哩哔哩).*$",
    re.I,
)
_SEARCH_ITEM = re.compile(
    r"^(\d+)\.\s+(.+)\n\s+(https?://\S+)(?:\n\s+(.+))?$",
    re.M,
)


def guess_search_query(url: str, hint: str = "") -> str:
    hint = (hint or "").strip()
    if hint:
        return hint[:120]
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = unquote(parsed.path or "")
    if any(k in host for k in ("kaoyan", "xdf.cn", "eol.cn", "scribd")):
        return "2024年考研数学一真题 答案解析"
    if "wenku.baidu.com" in host:
        return "2024考研数学一真题 PDF"
    if "zhihu.com" in host:
        return "2024考研数学一真题 知乎"
    if "baidu.com" in host:
        return "2024考研数学一真题"
    slug = path.rstrip("/").split("/")[-1].replace(".html", "").replace(".shtml", "")
    slug = re.sub(r"[_\-\d]{8,}", " ", slug)
    slug = re.sub(r"\s+", " ", slug).strip()
    if len(slug) >= 4 and not slug.isdigit():
        return slug[:80]
    return "考研数学一真题"


def _filter_noise_lines(text: str, max_lines: int = 25) -> str:
    lines: List[str] = []
    seen = set()
    for raw in text.splitlines():
        line = raw.strip()
        if len(line) < 8 or line in seen:
            continue
        if _NAV_LINE.match(line):
            continue
        if line.count(" ") > 12 and len(line) < 100:
            continue
        seen.add(line)
        lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def _parse_search_block(content: str) -> List[dict]:
    items = []
    for m in _SEARCH_ITEM.finditer(content):
        items.append({
            "title": m.group(2).strip(),
            "url": m.group(3).strip(),
            "snippet": (m.group(4) or "").strip(),
        })
    if items:
        return items
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("http://") or line.startswith("https://"):
            items.append({"title": line, "url": line, "snippet": ""})
    return items[:8]


def format_search_results(content: str, intro: str = "") -> str:
    body = content.split("联网搜索结果：", 1)[-1].strip()
    items = _parse_search_block(body)
    if not items:
        return intro or "未找到可用的联网搜索结果，请换关键词或提供 PDF/图片。"
    lines = [intro or "为你找到以下相关资料：", ""]
    for i, item in enumerate(items, 1):
        title = item["title"]
        url = item["url"]
        lines.append(f"{i}. [{title}]({url})")
        if item.get("snippet"):
            lines.append(f"   {item['snippet'][:120]}")
    lines.append("")
    lines.append("以上链接可打开查看完整真题；如需讲解某道题，请把题目文字或截图发给我。")
    return "\n".join(lines)


def format_fetch_results(content: str) -> str:
    if "403 Forbidden" in content or "403" in content and "站点拒绝" in content:
        search_part = content.split("联网搜索结果：", 1)
        if len(search_part) > 1:
            return format_search_results(
                "联网搜索结果：" + search_part[1],
                "该网页无法直接抓取（站点限制访问），已改用搜索为你整理替代来源：",
            )
        return (
            "该网页无法直接抓取（站点限制访问）。\n\n"
            "建议：换用教育在线、知乎专栏等可访问链接，或直接上传 PDF/题目截图。"
        )

    body = content.split("网页内容：", 1)[-1].strip()
    for marker in (
        "注意：该网页的主要正文以图片形式发布",
        "请不要说网页访问受限",
        "页面图片：",
    ):
        if marker in body:
            body = body.split(marker, 1)[0].strip()

    cleaned = _filter_noise_lines(body)
    if len(cleaned) < 40:
        http_imgs = [
            u for u in re.findall(r"https?://\S+", content)
            if "data:image" not in u and "logo" not in u.lower() and "share.png" not in u
        ][:5]
        lines = [
            "该页面正文主要是图片版试题，无法自动转成文字。",
            "",
            "你可以：",
            "1. 打开原网页查看或下载 PDF",
            "2. 把具体题目截图发给我，我来讲解",
        ]
        if http_imgs:
            lines.extend(["", "相关资源："])
            lines.extend(f"- {u}" for u in http_imgs)
        return "\n".join(lines)

    preview = cleaned[:800]
    if len(cleaned) > 800:
        preview += "\n…（已省略导航与页脚冗余内容）"
    return f"网页摘要：\n\n{preview}\n\n如需完整内容，请说明要查哪一部分，或提供 PDF/截图。"


def format_tool_content_for_user(content: str) -> str:
    text = (content or "").strip()
    if not text:
        return ""
    if text.startswith("联网搜索结果：") or "联网搜索结果：" in text:
        return format_search_results(text)
    if text.startswith("网页内容：") or "403 Forbidden" in text:
        return format_fetch_results(text)
    if len(text) > 1200:
        return text[:1200] + "\n…（内容已截断）"
    return text


def summarize_tool_messages(tool_contents: List[str]) -> str:
    parts: List[str] = []
    for raw in tool_contents:
        formatted = format_tool_content_for_user(raw)
        if formatted and formatted not in parts:
            parts.append(formatted)
    if not parts:
        return "工具已执行完成，但暂时没有可用正文。请换链接、上传 PDF，或把题目发给我。"
    if len(parts) == 1:
        return parts[0]
    return "\n\n---\n\n".join(parts)
