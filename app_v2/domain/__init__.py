"""
Dominio V2 — Contratos y tipos.

Exporta ports, modelos y value objects. Sin implementaciones.
Véase app_v2/domain/README.md.
"""

from app_v2.domain.ports import (
    AudioTransport,
    CallConfig,
    ConfigPort,
    ConfigPortError,
    LLMMessage,
    LLMPort,
    LLMRequest,
    STTConfig,
    STTPort,
    TTSRequest,
    TTSPort,
)
from app_v2.domain.models import LLMChunk
from app_v2.domain.value_objects import VoiceConfig

__all__ = [
    "AudioTransport",
    "CallConfig",
    "ConfigPort",
    "ConfigPortError",
    "LLMChunk",
    "LLMMessage",
    "LLMPort",
    "LLMRequest",
    "STTConfig",
    "STTPort",
    "TTSRequest",
    "TTSPort",
    "VoiceConfig",
]
