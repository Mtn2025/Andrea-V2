"""
Transport V2 para Telefonía (Telnyx/Twilio).

Implementa app_v2.domain.ports.AudioTransport para el WebSocket de telephony.
Misma lógica de mensajes que TelephonyTransport legacy (event "media", streamSid/stream_id);
close() cierra el WebSocket. Usado por routes_telephony cuando el handler usa Orchestrator V2.

Referencia legacy: app/adapters/telephony/transport.py (TelephonyTransport).
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 8 (Fase 4).
"""

import base64
import contextlib
import json
import logging
from typing import Any

from app_v2.domain.ports import AudioTransport

logger = logging.getLogger(__name__)


class V2TelephonyTransport(AudioTransport):
    """
    Implementación de AudioTransport (V2) para WebSocket Telnyx/Twilio.
    """

    def __init__(self, websocket: Any, protocol: str = "twilio") -> None:
        """
        Args:
            websocket: WebSocket (FastAPI/Starlette).
            protocol: "twilio" o "telnyx".
        """
        self._ws = websocket
        self._protocol = protocol
        self._stream_id: str | None = None

    def set_stream_id(self, stream_id: str) -> None:
        self._stream_id = stream_id

    async def send_audio(self, audio_data: bytes, sample_rate: int = 8000) -> None:
        if not self._stream_id:
            return
        try:
            b64 = base64.b64encode(audio_data).decode("utf-8")
            if self._protocol == "twilio":
                msg = {
                    "event": "media",
                    "streamSid": self._stream_id,
                    "media": {"payload": b64},
                }
            else:
                msg = {
                    "event": "media",
                    "stream_id": self._stream_id,
                    "media": {"payload": b64, "track": "inbound_track"},
                }
            await self._ws.send_text(json.dumps(msg))
        except Exception as e:
            logger.warning("V2TelephonyTransport send_audio failed: %s", e)

    async def send_json(self, data: dict[str, Any]) -> None:
        try:
            if self._stream_id and self._protocol == "twilio" and "streamSid" not in data:
                data = {**data, "streamSid": self._stream_id}
            await self._ws.send_text(json.dumps(data))
        except Exception as e:
            logger.warning("V2TelephonyTransport send_json failed: %s", e)

    async def close(self) -> None:
        with contextlib.suppress(Exception):
            await self._ws.close()
