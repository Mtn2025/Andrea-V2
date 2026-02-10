"""
GroqLLMAdapter — Implementación de LLMPort con Groq Chat Completions.

Streaming de texto; sin tools en Fase 3.

Referencia legacy: app/adapters/outbound/llm/groq_llm_adapter.py.
Decisión: Solo texto; sin circuit breaker ni decoradores de métricas en V2 (opcional después).
"""

import logging
from collections.abc import AsyncIterator

from groq import AsyncGroq

from app_v2.domain.models import LLMChunk
from app_v2.domain.ports import LLMRequest, LLMPort

logger = logging.getLogger(__name__)


class GroqLLMAdapter(LLMPort):
    """
    LLM vía Groq chat.completions (streaming).
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})
        try:
            stream = await self._client.chat.completions.create(
                model=request.model or self._model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason
                if getattr(delta, "content", None):
                    yield LLMChunk(text=delta.content)
                if finish_reason:
                    yield LLMChunk(text="", finish_reason=finish_reason)
        except Exception as e:
            logger.exception("Groq LLM failed")
            raise RuntimeError(f"LLM failed: {e!s}") from e
