"""
Aplicación V2 — Orquestación del flujo de voz.

Frames, pipeline, procesadores y orquestador. Sin implementaciones de proveedores.
Véase app_v2/application/README.md.
"""

from app_v2.application.frames import AudioFrame, Frame, TextFrame
from app_v2.application.pipeline import Pipeline
from app_v2.application.processor import Processor
from app_v2.application.orchestrator import Orchestrator

__all__ = [
    "AudioFrame",
    "Frame",
    "TextFrame",
    "Pipeline",
    "Processor",
    "Orchestrator",
]
