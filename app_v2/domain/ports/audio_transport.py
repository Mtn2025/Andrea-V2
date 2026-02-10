"""
Port: AudioTransport.

Interface para enviar audio y mensajes de control al cliente.
Las implementaciones (adapters) manejan WebSocket, SIP u otros protocolos.

Referencia legacy: app/domain/ports/audio_transport.py (solo como idea).
Decisión: Mantener los cuatro métodos; sin cambios de contrato.
"""

from abc import ABC, abstractmethod
from typing import Any


class AudioTransport(ABC):
    """
    Port para envío de audio y mensajes de control al cliente.

    Implementaciones: WebSocket (simulador), Twilio, Telnyx.
    """

    @abstractmethod
    async def send_audio(self, audio_data: bytes, sample_rate: int = 8000) -> None:
        """Envía bytes de audio al cliente."""
        ...

    @abstractmethod
    async def send_json(self, data: dict[str, Any]) -> None:
        """Envía un mensaje JSON de control al cliente."""
        ...

    @abstractmethod
    def set_stream_id(self, stream_id: str) -> None:
        """Establece el ID de flujo/llamada para el protocolo."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Cierra la conexión."""
        ...
