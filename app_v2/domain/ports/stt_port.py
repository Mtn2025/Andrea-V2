"""
Port: STTPort.

Interface para proveedores de Speech-to-Text.
Para el primer flujo V2 se usa transcripción "completa" (audio → texto), no streaming.

Referencia legacy: app/domain/ports/stt_port.py.
Decisión: Solo transcribe_audio async; no STTRecognizer ni streaming en Fase 1.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class STTConfig:
    """
    Configuración para reconocimiento STT.

    Usada por el adapter para idioma, formato de audio, etc.
    """
    language: str = "es-MX"
    sample_rate: int = 16000  # browser; 8000 para telephony
    channels: int = 1


class STTPort(ABC):
    """
    Port para proveedores de Speech-to-Text.

    En Fase 1: transcripción de un bloque de audio a texto completo.
    Streaming puede añadirse en fases posteriores.
    """

    @abstractmethod
    async def transcribe_audio(self, audio_bytes: bytes, config: STTConfig) -> str:
        """
        Transcribe audio a texto.

        Args:
            audio_bytes: Audio en bytes (formato según config).
            config: Configuración STT (idioma, sample rate, etc.).

        Returns:
            Texto transcrito.

        Raises:
            Excepciones del adapter en caso de fallo del proveedor.
        """
        ...
