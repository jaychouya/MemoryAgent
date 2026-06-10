"""API key validation for LLM configuration."""

from typing import Optional

_BLOCKED_FRAGMENTS = (
    "sk-test",
    "test-key",
    "your-api-key",
    "changeme",
    "placeholder",
    "example",
    "abcdefghijklmnopqrstuvwxyz",
)


def is_usable_api_key(key: Optional[str]) -> bool:
    k = (key or "").strip()
    if len(k) < 10:
        return False
    lowered = k.lower()
    return not any(fragment in lowered for fragment in _BLOCKED_FRAGMENTS)
