import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    token_count: int = 0


class RetrievedItem(BaseModel):
    text: str
    source: str  # "memory" | "document"
    score: float  # similarity/ranking score
    metadata: dict


class ContextPackage(BaseModel):
    system_prompt: str
    conversation: list[Message]
    retrieved: list[RetrievedItem]
    token_usage: dict[str, int]  # {"conversation": n, "retrieved": n, "total": n}