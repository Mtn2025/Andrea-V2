"""
Adaptadores outbound V2 — STT, LLM, TTS, Config.
"""

from app_v2.adapters.outbounds.config_adapter import ConfigAdapter
from app_v2.adapters.outbounds.stt_groq_adapter import GroqWhisperSTTAdapter
from app_v2.adapters.outbounds.llm_groq_adapter import GroqLLMAdapter
from app_v2.adapters.outbounds.tts_azure_adapter import AzureTTSAdapter

__all__ = [
    "ConfigAdapter",
    "GroqWhisperSTTAdapter",
    "GroqLLMAdapter",
    "AzureTTSAdapter",
]
