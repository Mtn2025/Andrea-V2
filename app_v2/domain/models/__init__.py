"""
Modelos de dominio V2.

Tipos usados por los ports o por la aplicación (chunks, etc.).
No incluye implementaciones ni acceso a BD/red.
"""

from app_v2.domain.models.llm_models import LLMChunk

__all__ = ["LLMChunk"]
