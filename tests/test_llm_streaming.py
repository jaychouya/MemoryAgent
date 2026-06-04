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
