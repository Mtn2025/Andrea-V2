"""
GroqWhisperSTTAdapter — Implementación de STTPort con Groq Whisper.

Transcripción one-shot (audio completo → texto). Mismo camino que el legacy
para transcribe_audio (legacy AzureSTTAdapter.transcribe_audio usa Groq Whisper).

Referencia legacy: app/adapters/outbound/stt/azure_stt_adapter.py (método transcribe_audio).
Decisión: Solo Groq Whisper; sin Azure STT en V2 Fase 3 para mantener dependencias mínimas.

Groq Whisper exige un archivo de audio válido (p. ej. WAV con cabecera). El front/envío
suele mandar PCM crudo; aquí empaquetamos PCM en WAV (cabecera RIFF) antes de enviar.

Validación de silencio: si el audio tiene RMS por debajo del umbral, no se llama a Whisper
(evita alucinaciones de transcripción en silencio/ruido).
"""

import io
import logging
import struct

import numpy as np
from groq import AsyncGroq

from app_v2.domain.ports import STTConfig, STTPort

logger = logging.getLogger(__name__)


# Mínimo de bytes PCM para enviar a Groq (evita 400 en fragmentos muy cortos/silencio).
# ~0.5 s a 16 kHz mono 16-bit = 16000 bytes.
MIN_PCM_BYTES_FOR_GROQ = 8_000

# RMS normalizado (0-1) por debajo del cual se considera silencio y no se llama a Whisper.
# Evita alucinaciones cuando el micrófono no captura voz real.
SILENCE_RMS_THRESHOLD = 0.01


def _pcm_bytes_from_audio(audio_bytes: bytes) -> bytes:
    """Extrae bytes PCM (16-bit) del buffer: si es WAV, salta cabecera RIFF."""
    if not audio_bytes:
        return b""
    if audio_bytes[:4] == b"RIFF":
        return audio_bytes[44:]
    return audio_bytes


def _compute_rms_normalized(pcm_bytes: bytes) -> float:
    """
    Calcula RMS del PCM 16-bit y lo normaliza a [0, 1].
    Retorna 0 si no hay suficientes muestras.
    """
    pcm = _pcm_bytes_from_audio(pcm_bytes)
    pcm = pcm[: (len(pcm) // 2) * 2]
    if len(pcm) < 2:
        return 0.0
    samples = np.frombuffer(pcm, dtype=np.int16)
    rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
    return float(rms / 32768.0)


def _is_silence(audio_bytes: bytes) -> bool:
    """True si el audio parece silencio (RMS bajo). No llama a Whisper en ese caso."""
    rms = _compute_rms_normalized(audio_bytes)
    return rms < SILENCE_RMS_THRESHOLD


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int, channels: int = 1) -> bytes:
    """
    Envuelve PCM 16-bit en cabecera WAV (RIFF) para que Groq Whisper acepte el archivo.
    """
    if not pcm_bytes:
        return b""
    # Asegurar longitud par (muestras de 2 bytes)
    pcm_bytes = pcm_bytes[: (len(pcm_bytes) // 2) * 2]
    if not pcm_bytes:
        return b""
    num_samples = len(pcm_bytes) // 2
    data_size = num_samples * 2
    byte_rate = sample_rate * channels * 2
    block_align = channels * 2
    # RIFF header: riff_id, file_size, wave_id, fmt_id, fmt_size, audio_format, num_channels, sample_rate, byte_rate, block_align, bits_per_sample, data_id, data_size
    file_size = 36 + data_size
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        file_size,
        b"WAVE",
        b"fmt ",
        16,  # fmt chunk size
        1,   # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        16,  # bits per sample
        b"data",
        data_size,
    )
    return header + pcm_bytes


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
        # Fragmentos demasiado cortos → Groq suele devolver 400; no enviar.
        if len(audio_bytes) < MIN_PCM_BYTES_FOR_GROQ and audio_bytes[:4] != b"RIFF":
            return ""
        # Groq exige archivo de audio válido. Si ya es WAV (RIFF), usar tal cual; si no, PCM → WAV.
        if audio_bytes[:4] == b"RIFF":
            wav_bytes = audio_bytes
        else:
            wav_bytes = _pcm_to_wav(
                audio_bytes,
                sample_rate=config.sample_rate,
                channels=config.channels,
            )
        if not wav_bytes:
            return ""
        # No enviar silencio a Whisper: evita alucinaciones de transcripción
        if _is_silence(audio_bytes):
            logger.debug(
                "STT skip: audio below RMS threshold (silence), size_bytes=%s",
                len(wav_bytes),
            )
            return ""
        # Duración aproximada: (tamaño - 44 cabecera WAV) / (sample_rate * 2) segundos (16-bit mono)
        data_bytes = max(0, len(wav_bytes) - 44)
        duration_sec = data_bytes / (config.sample_rate * 2) if config.sample_rate else 0
        logger.debug(
            "STT request: size_bytes=%s format=WAV duration_sec=%.2f model=%s",
            len(wav_bytes),
            duration_sec,
            self._model,
        )
        audio_file = io.BytesIO(wav_bytes)
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
