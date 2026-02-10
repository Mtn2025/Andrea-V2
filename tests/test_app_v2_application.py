"""
Tests de la capa application V2.

Verifican el flujo Orchestrator → Pipeline → Processors con mocks.
Sin dependencias de app/ ni de proveedores reales.
"""

import pytest

from app_v2.application import Orchestrator
from app_v2.application.verification_mocks import (
    MockAudioTransport,
    MockConfigPort,
    MockLLMPort,
    MockSTTPort,
    MockTTSPort,
)


@pytest.fixture
def mock_ports():
    transport = MockAudioTransport()
    stt = MockSTTPort(fixed_text="hola")
    llm = MockLLMPort(fixed_response="Hola, ¿en qué puedo ayudarte?")
    tts = MockTTSPort(fixed_audio=b"\x00\x00\x00\x00\x00\x00")
    config = MockConfigPort()
    return {
        "transport": transport,
        "stt": stt,
        "llm": llm,
        "tts": tts,
        "config": config,
    }


@pytest.mark.asyncio
async def test_orchestrator_process_audio_sends_audio(mock_ports):
    orch = Orchestrator(
        transport=mock_ports["transport"],
        stt_port=mock_ports["stt"],
        llm_port=mock_ports["llm"],
        tts_port=mock_ports["tts"],
        config_port=mock_ports["config"],
        client_type="browser",
    )
    await orch.start()
    await orch.process_audio(b"\x00\x00\x00\x00")
    await orch.stop()
    assert len(mock_ports["transport"].sent_audio) == 1
    assert mock_ports["transport"].sent_audio[0] == b"\x00\x00\x00\x00\x00\x00"
    assert mock_ports["transport"].closed is True


@pytest.mark.asyncio
async def test_orchestrator_start_loads_config(mock_ports):
    orch = Orchestrator(
        transport=mock_ports["transport"],
        stt_port=mock_ports["stt"],
        llm_port=mock_ports["llm"],
        tts_port=mock_ports["tts"],
        config_port=mock_ports["config"],
        client_type="browser",
    )
    await orch.start()
    assert orch._config is not None
    assert orch._config.client_type == "browser"
    assert orch._config.system_prompt == "Eres un asistente."
