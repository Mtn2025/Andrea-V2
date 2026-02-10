"""
ConfigAdapter — Implementación de ConfigPort con loader inyectado.

El orquestador recibe CallConfig (DTO). Quién construye ese DTO desde BD
queda fuera de app_v2: se inyecta una función async (client_type, agent_id) -> CallConfig.
Así app_v2 no depende de app.db ni app.services.

Referencia legacy: app/adapters/outbound/repositories/sqlalchemy_config_repository.py
y app/core/orchestrator_v2._load_config (get_agent_config + get_profile).
Decisión: Sin importar app; el entry point (app) proporciona el loader.
"""

from collections.abc import Awaitable, Callable

from app_v2.domain.ports import CallConfig, ConfigPort, ConfigPortError


class ConfigAdapter(ConfigPort):
    """
    Adaptador de configuración que delega en una función inyectada.
    """

    def __init__(
        self,
        loader: Callable[[str, int], Awaitable[CallConfig]],
    ) -> None:
        """
        Args:
            loader: Función async (client_type, agent_id) -> CallConfig.
                    La implementación (ej. lectura desde BD + perfil) vive fuera de app_v2.
        """
        self._loader = loader

    async def get_config_for_call(
        self,
        client_type: str,
        agent_id: int = 1,
    ) -> CallConfig:
        try:
            return await self._loader(client_type, agent_id)
        except Exception as e:
            raise ConfigPortError(f"Failed to load config: {e!s}") from e
