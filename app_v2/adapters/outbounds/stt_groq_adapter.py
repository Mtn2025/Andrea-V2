"""
GroqWhisperSTTAdapter — Implementación de STTPort con Groq Whisper.

Transcripción one-shot (audio completo → texto). Mismo camino que el legacy
para transcribe_audio (legacy AzureSTTAdapter.transcribe_audio usa Groq Whisper).

Referencia legacy: app/adapters/outbound/stt/azure_stt_adapter.py (método transcribe_audio).
Decisión: Solo Groq Whisper; sin Azure STT en V2 Fase 3 para mantener dependencias mínimas.
"""

import io
import logging

from groq import AsyncGroq

from app_v2.domain.ports import STTConfig, STTPort

logger = logging.getLogger(__name__)


class GroqWhisperSTTAdapter(STTPort):
    """
    STT vía Groq Whisper (audio → texto en una llamada).
    """

    def __init__(self, api_key: str, model: str = "whisper-large-v3") -> None:
        self._client = AsyncGroq(api_key=api_key)
        self._model = model

    async def transcribe_audio(self, audio_bytes: bytes, config: STTConfig) -> str:
        if not audio_bytes:
            return ""
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        try:
            transcription = await self._client.audio.transcriptions.create(
                file=(audio_file.name, audio_file.getvalue()),
                model=self._model,
                response_format="json",
                language=config.language.split("-")[0] if config.language else "es",
                temperature=0.0,
            )
            return (transcription.text or "").strip()
        except Exception as e:
            logger.exception("Groq Whisper STT failed")
            raise RuntimeError(f"STT failed: {e!s}") from e
