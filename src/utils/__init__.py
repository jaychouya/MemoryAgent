"""Utility functions and helpers."""


def as_int(value, default: int = 5) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
