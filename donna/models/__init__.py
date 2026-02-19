"""
donna.models — LLM backend package.

Exports:
    get_model()      — factory that returns the correct backend
    AbstractModel    — protocol for type-checking
    OllamaModel      — local Ollama backend
    GroqModel        — Groq cloud backend
    Message, Role, ToolCall, ToolSchema, AssistantMessage — data types
"""

from donna.models.base import (
    AbstractModel,
    AssistantMessage,
    Message,
    Role,
    ToolCall,
    ToolSchema,
)
from donna.models.ollama_backend import OllamaModel
from donna.models.groq_backend import GroqModel


def get_model(cloud: bool = False) -> AbstractModel:
    """Factory: return the appropriate LLM backend based on config.

    Parameters
    ----------
    cloud : bool
        If True, use Groq cloud.  Otherwise use local Ollama.
    """
    from donna.config import get_settings

    settings = get_settings()

    if cloud or settings.default_model == "groq":
        return GroqModel(
            api_key=settings.groq.api_key,
            model=settings.groq.model,
            temperature=settings.groq.temperature,
        )

    return OllamaModel(
        base_url=settings.ollama.base_url,
        model=settings.ollama.model,
        temperature=settings.ollama.temperature,
    )


__all__ = [
    "get_model",
    "AbstractModel",
    "AssistantMessage",
    "Message",
    "Role",
    "ToolCall",
    "ToolSchema",
    "OllamaModel",
    "GroqModel",
]
