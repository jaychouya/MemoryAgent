import pytest
from unittest.mock import AsyncMock, MagicMock

from src.backend.services import LLMService


@pytest.mark.asyncio
async def test_generate_response_stream_invokes_on_token():
    llm = LLMService(api_key="sk-test")
    tokens = []

    async def on_token(t: str):
        tokens.append(t)

    async def fake_stream():
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].finish_reason = None
        chunk1.choices[0].delta.content = "你"
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].finish_reason = "stop"
        chunk2.choices[0].delta.content = "好"
        yield chunk1
        yield chunk2

    mock_create = AsyncMock(return_value=fake_stream())
    llm.client = MagicMock()
    llm.client.chat.completions.create = mock_create

    result = await llm.generate_response_stream(
        messages=[{"role": "user", "content": "hi"}],
        on_token=on_token,
    )

    assert result["content"] == "你好"
    assert result.get("streamed") is True
    assert tokens == ["你", "好"]
    mock_create.assert_called_once()
    assert mock_create.call_args.kwargs.get("stream") is True


@pytest.mark.asyncio
async def test_generate_response_api_error_without_message_param():
    llm = LLMService(api_key="sk-test", model="gpt-4o-mini")
    llm.client = MagicMock()
    llm.client.chat.completions.create = AsyncMock(
        side_effect=Exception("Error code: 401 - invalid api key")
    )
    tools = [{
        "type": "function",
        "function": {"name": "memory_search", "parameters": {"type": "object", "properties": {}}},
    }]

    result = await llm.generate_response(
        message=None,
        messages=[{"role": "user", "content": "这是什么原因"}],
        tools=tools,
    )

    assert result["content"]
    assert "NoneType" not in result["content"]
    assert "API Key" in result["content"]


def test_parse_xml_web_fetch_tool_call():
    llm = LLMService()
    call = llm._parse_xml_tool_call(
        "<tool_call>\n"
        "<function=web_fetch>\n"
        "<parameter=url>https://example.com</parameter>\n"
        "<parameter=extractMode>text</parameter>\n"
        "<parameter=maxChars>15000</parameter>\n"
        "</function>\n"
        "</tool_call>"
    )

    assert call["function"]["name"] == "web_fetch"
    assert '"maxChars": 15000' in call["function"]["arguments"]


def test_clean_markdown_removes_xml_tool_call_blocks():
    llm = LLMService()
    text = llm._clean_markdown(
        "前文\n"
        "<tool_call><function=web_fetch><parameter=url>https://x.com</parameter></function></tool_call>\n"
        "后文"
    )

    assert "<tool_call>" not in text
    assert "web_fetch" not in text
    assert "前文" in text
    assert "后文" in text
