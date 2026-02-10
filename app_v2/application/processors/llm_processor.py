"""
LLMProcessor — Convierte TextFrame (user) en TextFrame (assistant).

Usa LLMPort.generate_stream; en Fase 2 se recolecta toda la respuesta en un solo texto.
Mantiene conversation_history (inyectada) actualizada.

Referencia legacy: app/processors/logic/llm.py (idea de history + stream).
Decisión: history mutable compartida con el orquestador; sin tools; collect completo.
"""

from app_v2.domain.ports import CallConfig, LLMMessage, LLMPort, LLMRequest
from app_v2.application.frames import Frame, TextFrame


class LLMProcessor:
    """
    Procesador LLM: texto usuario → texto asistente (vía stream recolectado).
    """

    def __init__(
        self,
        llm_port: LLMPort,
        config: CallConfig,
        conversation_history: list[LLMMessage],
    ) -> None:
        self._llm = llm_port
        self._config = config
        self._history = conversation_history

    async def process(self, frame: Frame) -> Frame | None:
        if not isinstance(frame, TextFrame) or frame.role != "user":
            return frame
        self._history.append(LLMMessage(role="user", content=frame.text))
        messages = list(self._history)
        request = LLMRequest(
            messages=messages,
            model=self._config.llm_model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
            system_prompt=None,
        )
        collected: list[str] = []
        async for chunk in self._llm.generate_stream(request):
            if chunk.text:
                collected.append(chunk.text)
        response_text = "".join(collected).strip()
        if not response_text:
            return None
        self._history.append(LLMMessage(role="assistant", content=response_text))
        return TextFrame(
            text=response_text,
            role="assistant",
            trace_id=frame.trace_id,
            timestamp=frame.timestamp,
        )
