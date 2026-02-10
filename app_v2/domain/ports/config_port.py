"""
Port: ConfigPort.

Interface para obtener la configuración de una llamada.
El retorno es siempre un DTO de dominio (CallConfig), nunca un modelo ORM.

Referencia legacy: app/domain/ports/config_repository_port.py (ConfigDTO) y
el uso en app/core/orchestrator_v2.py (get_agent_config + get_profile).
Decisión: Un solo método get_config_for_call(client_type, agent_id) que
devuelve CallConfig con todos los campos necesarios para el orquestador;
el adapter se encarga de leer BD, aplicar perfil y overlays.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CallConfig:
    """
    Configuración de una llamada (DTO de dominio).

    Contiene todo lo que el orquestador necesita para una sesión.
    El adapter construye este DTO desde BD + perfil (browser/twilio/telnyx).
    """
    # Identificación
    client_type: str  # "browser" | "twilio" | "telnyx"
    agent_id: int = 1

    # LLM
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 600
    system_prompt: str = ""
    first_message: str = ""
    first_message_mode: str = "speak-first"  # "speak-first" | "wait-for-user"

    # TTS / Voz
    voice_name: str = "es-MX-DaliaNeural"
    voice_language: str = "es-MX"
    voice_speed: float = 1.0
    voice_pitch: int = 0
    voice_volume: int = 100
    voice_style: str = "default"

    # STT
    stt_language: str = "es-MX"
    sample_rate: int = 16000  # 16000 browser; 8000 telephony
    silence_timeout_ms: int = 1000
    voice_pacing_ms: int = 0  # overlay por client_type en adapter

    # Comportamiento
    max_duration: int = 600
    idle_timeout: float = 30.0

    # Política de errores (Fase 1): mensaje de disculpa ante error crítico
    apology_message: str = "Lo sentimos, hemos tenido un problema. La llamada terminará."


class ConfigPortError(Exception):
    """Error al obtener o resolver la configuración (ej. agente no encontrado)."""
    pass


class ConfigPort(ABC):
    """
    Port para obtención de configuración de llamada.

    Retorna siempre CallConfig (DTO). El adapter lee de BD, aplica
    perfil (client_type) y overlays (pacing, silence, etc.).
    """

    @abstractmethod
    async def get_config_for_call(
        self,
        client_type: str,
        agent_id: int = 1,
    ) -> CallConfig:
        """
        Obtiene la configuración lista para una llamada.

        Args:
            client_type: "browser" | "twilio" | "telnyx".
            agent_id: Identificador del agente (por defecto 1).

        Returns:
            CallConfig con valores ya resueltos para ese perfil.

        Raises:
            ConfigPortError: Si el agente no existe o no se puede cargar.
        """
        ...
