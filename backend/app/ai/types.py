"""Shared types for the provider-independent AI layer."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ProviderId(str, Enum):
    XAI = "xai"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class AIMode(str, Enum):
    FREE_FIRST = "FREE_FIRST"
    PREMIUM = "PREMIUM"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


class ModelCapability(BaseModel):
    model_id: str
    provider: ProviderId
    context_window: int = 8192
    supports_tools: bool = False
    supports_json_mode: bool = True
    is_free: bool = False
    max_output_tokens: int = 4096
    cost_input_per_mtok: float = 0.0
    cost_output_per_mtok: float = 0.0


class CompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2048
    response_format: dict[str, Any] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UsageStats(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class CompletionResponse(BaseModel):
    content: str
    model: str
    provider: ProviderId
    usage: UsageStats = Field(default_factory=UsageStats)
    finish_reason: str | None = None
    raw: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] | None = None


class ProviderError(Exception):
    def __init__(self, provider: ProviderId, message: str, *, retryable: bool = False):
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"[{provider.value}] {message}")
