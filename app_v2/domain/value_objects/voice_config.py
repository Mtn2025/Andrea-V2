"""
Value object: VoiceConfig.

Configuración de voz inmutable y validada para TTS.
Se construye desde CallConfig (DTO de dominio); sin referencia a ORM.

Referencia legacy: app/domain/value_objects/voice_config.py.
Decisión: from_call_config(CallConfig); sin from_db_config. Validación en __post_init__.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app_v2.domain.ports import CallConfig

VoiceStyle = Literal["default", "cheerful", "sad", "angry", "friendly", "terrified", "excited", "hopeful"]


@dataclass(frozen=True)
class VoiceConfig:
    """
    Configuración de voz inmutable para TTS.

    Atributos:
        name: Nombre de la voz (ej. es-MX-DaliaNeural).
        speed: Velocidad (0.5–2.0).
        pitch: Tono en Hz (-100–+100).
        volume: Volumen (0–100).
        style: Estilo de habla.
        style_degree: Intensidad del estilo (0.01–2.0).
    """
    name: str
    speed: float = 1.0
    pitch: int = 0
    volume: int = 100
    style: VoiceStyle = "default"
    style_degree: float = 1.0

    def __post_init__(self) -> None:
        if not (0.5 <= self.speed <= 2.0):
            raise ValueError(f"speed must be in [0.5, 2.0], got {self.speed}")
        if not (-100 <= self.pitch <= 100):
            raise ValueError(f"pitch must be in [-100, 100], got {self.pitch}")
        if not (0 <= self.volume <= 100):
            raise ValueError(f"volume must be in [0, 100], got {self.volume}")
        if not (0.01 <= self.style_degree <= 2.0):
            raise ValueError(f"style_degree must be in [0.01, 2.0], got {self.style_degree}")

    @classmethod
    def from_call_config(cls, config: CallConfig) -> VoiceConfig:
        """
        Construye VoiceConfig desde el DTO de configuración de llamada.

        Args:
            config: CallConfig (del port de configuración).

        Returns:
            VoiceConfig inmutable.
        """
        return cls(
            name=config.voice_name,
            speed=config.voice_speed,
            pitch=config.voice_pitch,
            volume=config.voice_volume,
            style=config.voice_style if isinstance(config.voice_style, str) else "default",
            style_degree=1.0,
        )

    def to_tts_params(self) -> dict:
        """
        Parámetros para construir TTSRequest o SSML (adapter).

        Returns:
            Dict con voice_id, language, speed, pitch, volume.
        """
        return {
            "voice_id": self.name,
            "language": "es-MX",
            "speed": self.speed,
            "pitch": self.pitch,
            "volume": self.volume,
        }
