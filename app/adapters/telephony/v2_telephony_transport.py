"""
Transport V2 para Telefonía (Telnyx/Twilio).

Implementa app_v2.domain.ports.AudioTransport para el WebSocket de telephony.
Misma lógica de mensajes que TelephonyTransport legacy (event "media", streamSid/stream_id);
close() cierra el WebSocket. Usado por routes_telephony cuando el handler usa Orchestrator V2.

Robustez: comprueba que el WebSocket esté conectado antes de cada send; si está cerrado
loguea y no lanza, para evitar "Cannot call send once a close message has been sent".

Referencia legacy: app/adapters/telephony/transport.py (TelephonyTransport).
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 8 (Fase 4).
"""

import base64
import contextlib
import json
import logging
from typing import Any

from starlette.websockets import WebSocketState

from app_v2.domain.ports import AudioTransport

logger = logging.getLogger(__name__)

# Estado CONNECTED de Starlette para comprobar antes de enviar
_CONNECTED = WebSocketState.CONNECTED


class V2TelephonyTransport(AudioTransport):
    """
    Implementación de AudioTransport (V2) para WebSocket Telnyx/Twilio.
    Comprueba is_connected antes de cada send; si el WS está cerrado, loguea y no crashea.
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
        self._closed: bool = False

    def set_stream_id(self, stream_id: str) -> None:
        self._stream_id = stream_id

    def is_connected(self) -> bool:
        """True si el transport considera que el WebSocket sigue usable (no cerrado)."""
        if self._closed:
            return False
        try:
            state = getattr(self._ws, "application_state", None)
            return state == _CONNECTED
        except Exception:
            return False

    def _log_state(self, op: str) -> None:
        """Loguea el estado del WS antes de una operación (para diagnóstico)."""
        try:
            state = getattr(self._ws, "application_state", None)
            logger.debug(
                "V2TelephonyTransport %s: stream_id=%s closed=%s application_state=%s",
                op,
                self._stream_id,
                self._closed,
                state,
            )
        except Exception as e:
            logger.debug("V2TelephonyTransport %s: could not read state: %s", op, e)

    async def send_audio(self, audio_data: bytes, sample_rate: int = 8000) -> None:
        self._log_state("send_audio")
        if not self.is_connected():
            logger.warning(
                "V2TelephonyTransport send_audio skipped: WebSocket not connected (closed=%s)",
                self._closed,
            )
            return
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
            self._closed = True
            logger.warning(
                "V2TelephonyTransport send_audio failed (marking closed): %s",
                e,
                exc_info=False,
            )

    async def send_json(self, data: dict[str, Any]) -> None:
        self._log_state("send_json")
        if not self.is_connected():
            logger.warning(
                "V2TelephonyTransport send_json skipped: WebSocket not connected (closed=%s)",
                self._closed,
            )
            return
        try:
            payload = dict(data)
            if self._stream_id and self._protocol == "twilio" and "streamSid" not in payload:
                payload["streamSid"] = self._stream_id
            await self._ws.send_text(json.dumps(payload))
        except Exception as e:
            self._closed = True
            logger.warning(
                "V2TelephonyTransport send_json failed (marking closed): %s",
                e,
                exc_info=False,
            )

    async def close(self) -> None:
        if self._closed:
            logger.debug("V2TelephonyTransport close: already closed")
            return
        self._closed = True
        logger.debug("V2TelephonyTransport close: marking closed and closing WebSocket")
        with contextlib.suppress(Exception):
            await self._ws.close()
