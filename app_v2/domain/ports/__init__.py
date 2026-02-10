"""
Ports del dominio V2.

Interfaces (ABC) y tipos asociados. Sin implementaciones.
Véase app_v2/domain/README.md.
"""

from app_v2.domain.ports.audio_transport import AudioTransport
from app_v2.domain.ports.call_persistence_port import CallPersistencePort
from app_v2.domain.ports.config_port import CallConfig, ConfigPort, ConfigPortError
from app_v2.domain.ports.extraction_port import ExtractionPort
from app_v2.domain.ports.llm_port import LLMMessage, LLMPort, LLMRequest
from app_v2.domain.ports.stt_port import STTConfig, STTPort
from app_v2.domain.ports.tts_port import TTSRequest, TTSPort

__all__ = [
    "AudioTransport",
    "CallConfig",
    "CallPersistencePort",
    "ConfigPort",
    "ConfigPortError",
    "ExtractionPort",
    "LLMMessage",
    "LLMPort",
    "LLMRequest",
    "STTConfig",
    "STTPort",
    "TTSRequest",
    "TTSPort",
]
