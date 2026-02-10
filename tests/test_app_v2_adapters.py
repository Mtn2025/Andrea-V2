"""
Tests de los adaptadores V2.

ConfigAdapter con loader inyectado. Resto de adapters requieren credenciales (no mockeados aquí).
"""

import pytest

from app_v2.domain import CallConfig, ConfigPortError
from app_v2.adapters import ConfigAdapter


async def _loader(client_type: str, agent_id: int) -> CallConfig:
    return CallConfig(
        client_type=client_type,
        agent_id=agent_id,
        system_prompt="Test system prompt",
        stt_language="es-MX",
        sample_rate=16000,
    )


@pytest.mark.asyncio
async def test_config_adapter_returns_call_config():
    adapter = ConfigAdapter(loader=_loader)
    cfg = await adapter.get_config_for_call("browser", 1)
    assert cfg.client_type == "browser"
    assert cfg.agent_id == 1
    assert cfg.system_prompt == "Test system prompt"
    assert cfg.sample_rate == 16000


@pytest.mark.asyncio
async def test_config_adapter_raises_on_loader_failure():
    async def failing_loader(_ct: str, _aid: int) -> CallConfig:
        raise ValueError("DB unavailable")

    adapter = ConfigAdapter(loader=failing_loader)
    with pytest.raises(ConfigPortError) as exc_info:
        await adapter.get_config_for_call("browser", 1)
    assert "Failed to load config" in str(exc_info.value)
