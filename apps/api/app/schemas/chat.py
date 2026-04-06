from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatOptions(BaseModel):
    max_steps: int | None = Field(default=None, ge=1, le=20)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=8000)
    client_message_id: str | None = None
    mode: Literal["simple", "agent"] = "simple"
    options: ChatOptions | None = None


class MessageDTO(BaseModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime | None = None


class AgentInfo(BaseModel):
    mode: Literal["agent"]
    steps_used: int
    tools_called: list[str]


class UsageDTO(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_ms: int = 0


class ChatResponse(BaseModel):
    reply: str
    correlation_id: str
    session_id: str
    assistant_message_id: str
    usage: UsageDTO
    agent: AgentInfo | None = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageDTO]


class ErrorPayload(BaseModel):
    code: str
    message: str
    correlation_id: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorPayload
