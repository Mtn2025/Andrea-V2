"""
Loader de configuración para el orquestador V2.

Convierte la configuración de la app (BD + perfil + overlay) en CallConfig (DTO de app_v2).
Este módulo vive en app/ porque usa app.db, app.services y app.domain.config_logic.
El entry point (routes_simulator_v2) importa aquí y pasa el loader a ConfigAdapter.

Referencia: app/core/orchestrator_v2._load_config, app/domain/config_logic.apply_client_overlay.
Documentación: docs/APP_V2_BUILD_LOG.md (Paso 4).
"""

import logging
from typing import Any

from app.db.database import AsyncSessionLocal
from app.domain.config_logic import apply_client_overlay
from app.services.db_service import db_service

from app_v2.domain.ports import CallConfig

logger = logging.getLogger(__name__)


def _mutable_to_call_config(client_type: str, agent_id: int, p: Any) -> CallConfig:
    """Mapea objeto mutable (perfil + overlay) a CallConfig."""
    sample_rate = 16000 if client_type == "browser" else 8000
    return CallConfig(
        client_type=client_type,
        agent_id=agent_id,
        llm_provider=getattr(p, "llm_provider", None) or "groq",
        llm_model=getattr(p, "llm_model", None) or "llama-3.3-70b-versatile",
        temperature=float(getattr(p, "temperature", None) or 0.7),
        max_tokens=int(getattr(p, "max_tokens", None) or 600),
        system_prompt=(getattr(p, "system_prompt", None) or "").strip(),
        first_message=(getattr(p, "first_message", None) or "").strip(),
        first_message_mode=getattr(p, "first_message_mode", None) or "speak-first",
        voice_name=getattr(p, "voice_name", None) or "es-MX-DaliaNeural",
        voice_language=getattr(p, "voice_language", None) or "es-MX",
        voice_speed=float(getattr(p, "voice_speed", None) or 1.0),
        voice_pitch=int(getattr(p, "voice_pitch", None) or 0),
        voice_volume=int(getattr(p, "voice_volume", None) or 100),
        voice_style=getattr(p, "voice_style", None) or "default",
        stt_language=getattr(p, "stt_language", None) or "es-MX",
        sample_rate=sample_rate,
        silence_timeout_ms=int(getattr(p, "silence_timeout_ms", None) or 1000),
        voice_pacing_ms=int(getattr(p, "voice_pacing_ms", None) or 0),
        max_duration=int(getattr(p, "max_duration", None) or 600),
        idle_timeout=float(getattr(p, "idle_timeout", None) or 30.0),
        apology_message=(getattr(p, "apology_message", None) or "").strip()
        or "Lo sentimos, hemos tenido un problema. La llamada terminará.",
    )


async def load_config_for_call(client_type: str, agent_id: int = 1) -> CallConfig:
    """
    Carga la configuración para una llamada y la devuelve como CallConfig (app_v2).

    Usa BD (get_agent_config), get_profile(client_type) y apply_client_overlay.
    """
    async with AsyncSessionLocal() as session:
        orm_config = await db_service.get_agent_config(session)
        if not orm_config:
            raise ValueError("Agent config not found")
        profile = orm_config.get_profile(client_type)
        mutable: Any = type("Profile", (), {})()
        for key, value in profile.model_dump().items():
            if value is not None:
                setattr(mutable, key, value)
        apply_client_overlay(mutable, client_type)
        return _mutable_to_call_config(client_type, agent_id, mutable)
