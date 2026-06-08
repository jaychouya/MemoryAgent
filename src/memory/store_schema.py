"""Validation for MCP/HTTP memory_store payloads."""

from typing import Optional, Tuple

from pydantic import BaseModel, Field, field_validator

_ALLOWED_TYPES = {"user", "feedback", "project", "reference"}


class MemoryStoreInput(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=6, max_length=8000)
    memory_type: str = "user"
    description: Optional[str] = Field(default=None, max_length=500)
    project_id: Optional[str] = Field(default=None, max_length=256)
    supersedes: Optional[str] = Field(default=None, max_length=256)
    source_session_id: Optional[str] = Field(default=None, max_length=256)
    source_turn: Optional[int] = Field(default=None, ge=0)
    source_quote: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("memory_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        t = (v or "user").lower().strip()
        if t not in _ALLOWED_TYPES:
            raise ValueError(f"memory_type must be one of {_ALLOWED_TYPES}")
        return t

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 6:
            raise ValueError("content too short after strip")
        return s


def validate_store_payload(
    user_id: str,
    content: str,
    memory_type: str = "user",
    description: Optional[str] = None,
    project_id: Optional[str] = None,
    supersedes: Optional[str] = None,
    source_session_id: Optional[str] = None,
    source_turn: Optional[int] = None,
    source_quote: Optional[str] = None,
) -> Tuple[Optional[MemoryStoreInput], Optional[str]]:
    try:
        return MemoryStoreInput(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            description=description,
            project_id=project_id,
            supersedes=supersedes,
            source_session_id=source_session_id,
            source_turn=source_turn,
            source_quote=source_quote,
        ), None
    except Exception as e:
        return None, str(e)
