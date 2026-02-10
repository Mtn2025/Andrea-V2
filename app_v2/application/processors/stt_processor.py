"""
STTProcessor — Convierte AudioFrame en TextFrame (rol user).

Usa STTPort.transcribe_audio(audio_bytes, STTConfig).
Solo procesa AudioFrame; el resto se devuelve sin cambio para no romper la cadena.

Referencia legacy: app/processors/logic/stt.py (idea de usar STT y emitir texto).
Decisión: Un solo tipo de entrada (AudioFrame); salida TextFrame(role="user").
"""

from app_v2.domain.ports import CallConfig, STTConfig, STTPort
from app_v2.application.frames import AudioFrame, Frame, TextFrame


class STTProcessor:
    """
    Procesador STT: audio → texto (rol user).
    """

    def __init__(self, stt_port: STTPort, config: CallConfig) -> None:
        self._stt = stt_port
        self._config = config

    async def process(self, frame: Frame) -> Frame | None:
        if not isinstance(frame, AudioFrame):
            return frame
        stt_config = STTConfig(
            language=self._config.stt_language,
            sample_rate=self._config.sample_rate,
        )
        text = await self._stt.transcribe_audio(frame.data, stt_config)
        if not text or not text.strip():
            return None
        return TextFrame(
            text=text.strip(),
            role="user",
            trace_id=frame.trace_id,
            timestamp=frame.timestamp,
        )
