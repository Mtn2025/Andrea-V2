"""
Frames V2 — Unidades de datos que circulan por el pipeline.

Solo los necesarios para el flujo audio → STT → LLM → TTS → audio.
Sin SystemFrame, ControlFrame ni prioridades en Fase 2.

Referencia legacy: app/core/frames.py (idea de Frame con trace_id).
Decisión: Base Frame con trace_id y timestamp; AudioFrame y TextFrame con payload mínimo.
"""

import time
import uuid
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Frame:
    """
    Frame base: identificador de traza y timestamp.

    Atributos:
        trace_id: Identificador del turno o llamada (para logs).
        timestamp: Momento de creación (Unix).
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


@dataclass(kw_only=True)
class AudioFrame(Frame):
    """
    Frame de audio: bytes y formato.

    Usado como entrada (audio del usuario) y salida (audio del TTS).
    """
    data: bytes
    sample_rate: int = 16000
    channels: int = 1


@dataclass(kw_only=True)
class TextFrame(Frame):
    """
    Frame de texto: contenido y rol (user | assistant).

    Usado tras STT (rol user) y tras LLM (rol assistant).
    """
    text: str
    role: str = "user"  # "user" | "assistant"
