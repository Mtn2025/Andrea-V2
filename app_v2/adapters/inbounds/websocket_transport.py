"""
WebSocketTransport — Implementación de AudioTransport sobre WebSocket.

Envía audio en base64 dentro de JSON { type: "audio", data: "<base64>" }
y mensajes de control como JSON. Compatible con el simulador del frontend.

Referencia legacy: app/adapters/simulator/transport.py (SimulatorTransport).
Decisión: Misma forma de mensaje; sin importar app; WebSocket tipado desde fastapi.
"""

import base64
import contextlib
import json
import logging
from typing import Any

from app_v2.domain.ports import AudioTransport

logger = logging.getLogger(__name__)


class WebSocketTransport(AudioTransport):
    """
    Transport que usa un WebSocket (FastAPI/Starlette) para enviar audio y JSON.
    """

    def __init__(self, websocket: Any) -> None:
        """
        Args:
            websocket: Objeto con send_text(bytes|str) y opcionalmente receive_*.
                      Típicamente fastapi.WebSocket.
        """
        self._ws = websocket

    async def send_audio(self, audio_data: bytes, sample_rate: int = 8000) -> None:
        try:
            b64 = base64.b64encode(audio_data).decode("utf-8")
            await self._ws.send_text(json.dumps({"type": "audio", "data": b64}))
        except Exception as e:
            logger.warning("WebSocketTransport send_audio failed: %s", e)

    async def send_json(self, data: dict[str, Any]) -> None:
        with contextlib.suppress(Exception):
            await self._ws.send_text(json.dumps(data))

    def set_stream_id(self, stream_id: str) -> None:
        self._stream_id = stream_id  # noqa: attribute defined in send_* usage if needed

    async def close(self) -> None:
        with contextlib.suppress(Exception):
            await self._ws.close()
