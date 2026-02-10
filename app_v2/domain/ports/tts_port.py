"""
Port: TTSPort.

Interface para proveedores de Text-to-Speech.
Síntesis de texto a audio (un bloque).

Referencia legacy: app/domain/ports/tts_port.py.
Decisión: Solo synthesize(request) -> bytes en Fase 1; sin synthesize_ssml ni
get_available_voices/get_voice_styles en el contrato inicial.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSRequest:
    """
    Solicitud de síntesis de voz.

    Parámetros genéricos; opciones por proveedor en provider_options si se necesitan.
    """
    text: str
    voice_id: str
    language: str = "es-MX"
    speed: float = 1.0
    pitch: int = 0
    volume: int = 100


class TTSPort(ABC):
    """
    Port para proveedores de Text-to-Speech.

    En Fase 1: synthesize devuelve audio completo en bytes.
    """

    @abstractmethod
    async def synthesize(self, request: TTSRequest) -> bytes:
        """
        Sintetiza texto a audio.

        Args:
            request: Texto, voz, idioma y parámetros de expresión.

        Returns:
            Audio en bytes (formato según el adapter/proveedor).
        """
        ...
