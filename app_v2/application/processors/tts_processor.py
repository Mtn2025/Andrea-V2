"""
TTSProcessor — Convierte TextFrame (assistant) en AudioFrame.

Usa TTSPort.synthesize con TTSRequest construido desde CallConfig (vía VoiceConfig).
Solo procesa TextFrame con role assistant; el resto se devuelve sin cambio.

Referencia legacy: app/processors/logic/tts.py (idea de config → TTSRequest).
Decisión: VoiceConfig.from_call_config(config); TTSRequest con text + to_tts_params().
"""

from app_v2.domain.ports import CallConfig, TTSRequest, TTSPort
from app_v2.domain.value_objects import VoiceConfig
from app_v2.application.frames import AudioFrame, Frame, TextFrame


class TTSProcessor:
    """
    Procesador TTS: texto asistente → audio.
    """

    def __init__(self, tts_port: TTSPort, config: CallConfig) -> None:
        self._tts = tts_port
        self._config = config

    async def process(self, frame: Frame) -> Frame | None:
        if not isinstance(frame, TextFrame) or frame.role != "assistant":
            return frame
        if not frame.text or not frame.text.strip():
            return None
        voice = VoiceConfig.from_call_config(self._config)
        params = voice.to_tts_params()
        request = TTSRequest(
            text=frame.text.strip(),
            voice_id=params["voice_id"],
            language=params["language"],
            speed=params["speed"],
            pitch=params["pitch"],
            volume=params["volume"],
        )
        audio_bytes = await self._tts.synthesize(request)
        if not audio_bytes:
            return None
        return AudioFrame(
            data=audio_bytes,
            sample_rate=self._config.sample_rate,
            trace_id=frame.trace_id,
            timestamp=frame.timestamp,
        )
