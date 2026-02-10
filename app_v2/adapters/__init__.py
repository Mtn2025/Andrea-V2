"""
Adaptadores V2 — Implementaciones de los ports del dominio.

Outbounds: STT, LLM, TTS, Config. Inbounds: WebSocket transport.
Véase app_v2/adapters/README.md.
"""

from app_v2.adapters.outbounds import (
    ConfigAdapter,
    GroqLLMAdapter,
    GroqWhisperSTTAdapter,
    AzureTTSAdapter,
)
from app_v2.adapters.inbounds import WebSocketTransport

__all__ = [
    "ConfigAdapter",
    "GroqLLMAdapter",
    "GroqWhisperSTTAdapter",
    "AzureTTSAdapter",
    "WebSocketTransport",
]
