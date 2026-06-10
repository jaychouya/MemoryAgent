from src.agent.tool_result_format import (
    format_fetch_results,
    format_search_results,
    guess_search_query,
    summarize_tool_messages,
)


def test_guess_search_query_from_kaoyan_url():
    q = guess_search_query("https://kaoyan.xdf.cn/202312/13554664.html")
    assert "考研" in q or "数学" in q


def test_guess_search_query_prefers_hint():
    assert guess_search_query("https://x.com", "2024数一第3题") == "2024数一第3题"


def test_format_search_results_markdown_links():
    raw = (
        "联网搜索结果：\n\n"
        "1. 2024考研数学一真题\n"
        "   https://kaoyan.eol.cn/shiti/shuxue/example.shtml\n"
        "   完整版解析\n\n"
    )
    out = format_search_results(raw)
    assert "[2024考研数学一真题]" in out
    assert "kaoyan.eol.cn" in out
    assert "根据工具结果整理" not in out


def test_format_fetch_403_uses_search_not_url_garbage():
    raw = (
        "目标网页返回 403 Forbidden（https://wenku.baidu.com/view/x.html），无法直接抓取。\n\n"
        "已用关键词「2024考研数学一真题 PDF」联网搜索替代来源：\n\n"
        "联网搜索结果：\n\n"
        "1. 2024年考研数学（一）真题\n"
        "   https://kaoyan.eol.cn/shiti/example.shtml\n\n"
    )
    out = format_fetch_results(raw)
    assert "站点限制" in out or "无法直接抓取" in out
    assert "huggingface" not in out
    assert "kaoyan.eol.cn" in out


def test_format_fetch_image_page_no_base64():
    raw = (
        "网页内容：\n\n短内容\n\n"
        "注意：该网页的主要正文以图片形式发布；\n"
        "页面图片：\n"
        "logo: https://images.xdf.cn/logo.png\n"
        "data:image/png;base64,AAAA\n"
    )
    out = format_fetch_results(raw)
    assert "base64" not in out
    assert "截图" in out or "PDF" in out


def test_summarize_strips_raw_dump_header():
    out = summarize_tool_messages([
        "联网搜索结果：\n\n1. 真题\n   https://example.com/a\n\n"
    ])
    assert "根据工具结果整理如下" not in out
    assert "example.com" in out
