"""
Port: LLMPort.

Interface para proveedores de LLM.
Incluye tipos de solicitud (LLMRequest, LLMMessage); el chunk de respuesta
(LLMChunk) está en domain/models para uso compartido.

Referencia legacy: app/domain/ports/llm_port.py.
Decisión: generate_stream que yield LLMChunk; sin get_available_models ni
is_model_safe_for_voice en Fase 1. Sin tools en el primer slice.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app_v2.domain.models import LLMChunk


@dataclass
class LLMMessage:
    """Mensaje en la conversación (system, user, assistant)."""
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMRequest:
    """Solicitud de generación al LLM."""
    messages: list[LLMMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 600
    system_prompt: str | None = None


class LLMPort(ABC):
    """
    Port para proveedores de LLM.

    En Fase 1: solo streaming de texto (LLMChunk con text).
    Function calling / tools en fases posteriores.
    """

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        """
        Genera respuesta en streaming.

        Args:
            request: Mensajes y parámetros de generación.

        Yields:
            LLMChunk con texto (y opcionalmente finish_reason al final).
        """
        ...
