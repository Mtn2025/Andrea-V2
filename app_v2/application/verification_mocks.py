"""
Mocks mínimos para verificar el flujo application V2 sin proveedores reales.

Solo para uso en verificación/tests; no forma parte del runtime.
Cada mock implementa el port correspondiente del dominio.
"""

from collections.abc import AsyncIterator

from app_v2.domain import (
    AudioTransport,
    CallConfig,
    ConfigPort,
    ConfigPortError,
    LLMChunk,
    LLMMessage,
    LLMPort,
    LLMRequest,
    STTConfig,
    STTPort,
    TTSRequest,
    TTSPort,
)


class MockAudioTransport(AudioTransport):
    """Transport que acumula el audio enviado (para aserciones)."""

    def __init__(self) -> None:
        self.sent_audio: list[bytes] = []
        self.stream_id: str | None = None
        self.closed = False

    async def send_audio(self, audio_data: bytes, sample_rate: int = 8000) -> None:
        self.sent_audio.append(audio_data)

    async def send_json(self, data: dict) -> None:
        pass

    def set_stream_id(self, stream_id: str) -> None:
        self.stream_id = stream_id

    async def close(self) -> None:
        self.closed = True


class MockSTTPort(STTPort):
    """STT que devuelve texto fijo."""

    def __init__(self, fixed_text: str = "hola") -> None:
        self.fixed_text = fixed_text

    async def transcribe_audio(self, audio_bytes: bytes, config: STTConfig) -> str:
        return self.fixed_text


class MockLLMPort(LLMPort):
    """LLM que devuelve un chunk de texto fijo."""

    def __init__(self, fixed_response: str = "Hola, ¿en qué puedo ayudarte?") -> None:
        self.fixed_response = fixed_response

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        yield LLMChunk(text=self.fixed_response, finish_reason=None)
        yield LLMChunk(text="", finish_reason="stop")


class MockTTSPort(TTSPort):
    """TTS que devuelve bytes fijos (ej. silencio o marcador)."""

    def __init__(self, fixed_audio: bytes = b"\x00\x00\x00\x00") -> None:
        self.fixed_audio = fixed_audio

    async def synthesize(self, request: TTSRequest) -> bytes:
        return self.fixed_audio


class MockConfigPort(ConfigPort):
    """Config que devuelve un CallConfig por defecto."""

    async def get_config_for_call(
        self,
        client_type: str = "browser",
        agent_id: int = 1,
    ) -> CallConfig:
        return CallConfig(
            client_type=client_type,
            agent_id=agent_id,
            system_prompt="Eres un asistente.",
            stt_language="es-MX",
            sample_rate=16000,
        )
