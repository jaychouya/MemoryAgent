"""Tests for chat tier and memory model routing."""

from src.backend.model_routing import pick_memory_model, pick_model_for_tier


def test_pick_fast_tier_from_pool():
    models = ["gpt-4o", "gpt-4o-mini", "o3"]
    assert pick_model_for_tier("gpt-4o", "fast", models) == "gpt-4o-mini"


def test_pick_deep_tier_from_pool():
    models = ["qwen-turbo", "qwen-plus", "qwen-max"]
    assert pick_model_for_tier("qwen-turbo", "deep", models) == "qwen-max"


def test_balanced_keeps_default():
    assert pick_model_for_tier("mimo-v2.5-pro", "balanced", ["mimo-v2.5"]) == "mimo-v2.5-pro"


def test_pick_memory_model_downgrades_pro():
    assert pick_memory_model("mimo-v2.5-pro") == "mimo-v2.5"
    assert "lite" in pick_memory_model("doubao-2.0-pro-32k").lower() or "flash" in pick_memory_model("doubao-2.0-pro-32k").lower()
