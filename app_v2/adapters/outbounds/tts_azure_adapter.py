"""
AzureTTSAdapter — Implementación de TTSPort con Azure Speech SDK.

Síntesis one-shot (texto → audio bytes). Formato configurable (16kHz PCM para browser).

Referencia legacy: app/adapters/outbound/tts/azure_tts_adapter.py.
Decisión: Solo synthesize; formato de salida por constructor (pcm_16k | mulaw_8k).
Salida vía archivo temporal para compatibilidad multiplataforma (result.audio_data no siempre disponible).
"""

import asyncio
import contextlib
import logging
import os
import tempfile

import azure.cognitiveservices.speech as speechsdk

from app_v2.domain.ports import TTSRequest, TTSPort

logger = logging.getLogger(__name__)


def _build_ssml(request: TTSRequest) -> str:
    """Construye SSML mínimo para Azure."""
    rate = str(request.speed)
    pitch_val = getattr(request, "pitch", 0) or 0
    pitch = f"{pitch_val:+.0f}Hz" if pitch_val != 0 else "0Hz"
    volume = str(getattr(request, "volume", 100))
    return (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{request.language}">'
        f'<voice name="{request.voice_id}">'
        f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">{request.text}</prosody>'
        f"</voice></speak>"
    )


class AzureTTSAdapter(TTSPort):
    """
    TTS vía Azure Speech SDK (SSML, bloque completo).
    """

    def __init__(
        self,
        api_key: str,
        region: str,
        output_format: str = "pcm_16k",
    ) -> None:
        """
        Args:
            api_key: Azure Speech key.
            region: Azure region (ej. eastus).
            output_format: "pcm_16k" (browser) o "mulaw_8k" (telephony).
        """
        self._speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        if output_format == "pcm_16k":
            self._speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
            )
        else:
            self._speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw8Khz8BitMonoMULaw
            )

    def _get_synthesizer(self, voice_name: str, output_path: str) -> speechsdk.SpeechSynthesizer:
        self._speech_config.speech_synthesis_voice_name = voice_name
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
        return speechsdk.SpeechSynthesizer(
            speech_config=self._speech_config,
            audio_config=audio_config,
        )

    async def synthesize(self, request: TTSRequest) -> bytes:
        logger.debug(
            "TTS request: voice_id=%s language=%s text_len=%s",
            request.voice_id,
            request.language,
            len(request.text),
        )
        ssml = _build_ssml(request)
        fd, path = tempfile.mkstemp(suffix=".raw")
        os.close(fd)
        try:
            loop = asyncio.get_running_loop()

            def _blocking() -> None:
                syn = self._get_synthesizer(request.voice_id, path)
                result = syn.speak_ssml_async(ssml).get()
                if result.reason == speechsdk.ResultReason.Canceled:
                    det = result.cancellation_details
                    raise RuntimeError(f"Azure TTS canceled: {det.reason} - {det.error_details}")
                if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                    raise RuntimeError(f"Azure TTS unexpected reason: {result.reason}")

            await loop.run_in_executor(None, _blocking)
            with open(path, "rb") as f:
                return f.read()
        finally:
            with contextlib.suppress(FileNotFoundError, OSError):
                os.unlink(path)
