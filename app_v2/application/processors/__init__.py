"""
Procesadores V2 — Implementaciones de Processor.

Cada uno usa un port del dominio (STT, LLM, TTS) y CallConfig.
Véase app_v2/application/README.md.
"""

from app_v2.application.processors.stt_processor import STTProcessor
from app_v2.application.processors.llm_processor import LLMProcessor
from app_v2.application.processors.tts_processor import TTSProcessor

__all__ = ["STTProcessor", "LLMProcessor", "TTSProcessor"]
