"""
Modelo: LLMChunk.

Fragmento de respuesta del LLM en streaming.
En Fase 1 solo texto; finish_reason indica fin de turno.
Function calling (chunks con tool_call) en fases posteriores.

Referencia legacy: app/domain/models/llm_models.py.
Decisión: Solo text y finish_reason; sin function_call en Fase 1.
"""

from dataclasses import dataclass


@dataclass
class LLMChunk:
    """
    Un chunk de la respuesta del LLM en streaming.

    Atributos:
        text: Fragmento de texto (puede ser vacío).
        finish_reason: None hasta el último chunk; luego "stop" | "length" | etc.
    """
    text: str = ""
    finish_reason: str | None = None
