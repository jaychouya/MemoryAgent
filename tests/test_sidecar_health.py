"""Tests for sidecar health checklist."""

import pytest

from src.backend.sidecar_health import build_sidecar_health


@pytest.mark.asyncio
async def test_build_sidecar_health_shape():
    h = await build_sidecar_health()
    assert "scope" in h
    assert "checks" in h
    assert isinstance(h["checks"], list)
    assert "tips" in h
    assert "user_id" in h["scope"]
