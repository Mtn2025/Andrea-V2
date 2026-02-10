#!/usr/bin/env python3
"""
Test del orquestador V2 con mocks — simula una llamada completa sin servicios reales.

Uso (desde la raíz del proyecto):
    python test_orchestrator.py

No requiere Docker ni variables de entorno. Imprime cada paso del flujo en consola.
"""

import asyncio
import sys
from pathlib import Path

# Asegurar que app_v2 sea importable (raíz del proyecto en sys.path)
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from collections.abc import AsyncIterator

from app_v2.application.orchestrator import Orchestrator
from app_v2.domain.ports import (
    AudioTransport,
    CallConfig,
    CallPersistencePort,
    ConfigPort,
    ConfigPortError,
    ExtractionPort,
    LLMMessage,
    LLMPort,
    LLMRequest,
    STTConfig,
    STTPort,
    TTSRequest,
    TTSPort,
)
from app_v2.domain.models import LLMChunk


# -----------------------------------------------------------------------------
# Mocks con impresión en consola
# -----------------------------------------------------------------------------

class MockConfigPort(ConfigPort):
    """Devuelve CallConfig fijo e imprime la petición."""

    async def get_config_for_call(
        self,
        client_type: str = "browser",
        agent_id: int = 1,
    ) -> CallConfig:
        print("  [Config] get_config_for_call(client_type=%r, agent_id=%s)" % (client_type, agent_id))
        config = CallConfig(
            client_type=client_type,
            agent_id=agent_id,
            system_prompt="Eres un asistente de prueba. Responde de forma breve.",
            stt_language="es-MX",
            sample_rate=16000,
            apology_message="Lo sentimos, hemos tenido un problema. La llamada terminará.",
        )
        print("  [Config] -> CallConfig(system_prompt=..., sample_rate=16000)")
        return config


class MockSTTPort(STTPort):
    """Devuelve texto fijo e imprime cada transcripción."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = responses or ["Hola, buenos días", "Necesito información sobre el horario"]
        self._index = 0

    async def transcribe_audio(self, audio_bytes: bytes, config: STTConfig) -> str:
        text = self._responses[self._index % len(self._responses)]
        self._index += 1
        print("  [STT] transcribe_audio(%d bytes) -> %r" % (len(audio_bytes), text))
        return text


class MockLLMPort(LLMPort):
    """Devuelve respuestas fijas en streaming e imprime."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = responses or [
            "Hola, ¿en qué puedo ayudarte hoy?",
            "Claro, el horario de atención es de 9 a 18 h.",
        ]
        self._index = 0

    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        text = self._responses[self._index % len(self._responses)]
        self._index += 1
        print("  [LLM] generate_stream(%d messages) -> %r" % (len(request.messages), text[:50] + "..." if len(text) > 50 else text))
        yield LLMChunk(text=text, finish_reason=None)
        yield LLMChunk(text="", finish_reason="stop")


class MockTTSPort(TTSPort):
    """Devuelve audio ficticio (bytes) e imprime."""

    async def synthesize(self, request: TTSRequest) -> bytes:
        # Simular ~0.1 s de “audio” (1600 muestras 16-bit a 16 kHz)
        fake_audio = b"\x00\x01\x00\xff" * 400
        print("  [TTS] synthesize(%r...) -> %d bytes" % (request.text[:30], len(fake_audio)))
        return fake_audio


class MockTransport(AudioTransport):
    """Transport que imprime cada envío y cierre."""

    def __init__(self) -> None:
        self.sent_audio_chunks: list[int] = []
        self.sent_jsons: list[dict] = []
        self.closed = False

    async def send_audio(self, audio_data: bytes, sample_rate: int = 8000) -> None:
        self.sent_audio_chunks.append(len(audio_data))
        print("  [Transport] send_audio(%d bytes, sample_rate=%s)" % (len(audio_data), sample_rate))

    async def send_json(self, data: dict) -> None:
        self.sent_jsons.append(data)
        print("  [Transport] send_json(%s)" % (list(data.keys()),))

    def set_stream_id(self, stream_id: str) -> None:
        print("  [Transport] set_stream_id(%r)" % (stream_id,))

    async def close(self) -> None:
        self.closed = True
        print("  [Transport] close()")


class MockPersistencePort(CallPersistencePort):
    """Simula persistencia e imprime cada operación."""

    def __init__(self) -> None:
        self._call_id_counter = 0
        self._calls: dict[int, dict] = {}

    async def create_call(self, stream_id: str, client_type: str) -> int | None:
        self._call_id_counter += 1
        call_id = self._call_id_counter
        self._calls[call_id] = {"stream_id": stream_id, "client_type": client_type, "transcripts": [], "extraction": None}
        print("  [Persistence] create_call(stream_id=%r, client_type=%r) -> call_id=%s" % (stream_id, client_type, call_id))
        return call_id

    async def save_transcripts(
        self,
        call_id: int,
        items: list[tuple[str, str]],
    ) -> None:
        if call_id in self._calls:
            self._calls[call_id]["transcripts"] = items
        print("  [Persistence] save_transcripts(call_id=%s, %d items)" % (call_id, len(items)))

    async def update_call_extraction(self, call_id: int, extracted_data: dict) -> None:
        if call_id in self._calls:
            self._calls[call_id]["extraction"] = extracted_data
        print("  [Persistence] update_call_extraction(call_id=%s, keys=%s)" % (call_id, list(extracted_data.keys())))

    async def end_call(self, call_id: int) -> None:
        print("  [Persistence] end_call(call_id=%s)" % (call_id,))


class MockExtractionPort(ExtractionPort):
    """Devuelve datos de extracción ficticios e imprime."""

    async def extract(
        self,
        stream_id: str,
        items: list[tuple[str, str]],
    ) -> dict:
        result = {
            "summary": "Llamada de prueba: usuario preguntó por horario.",
            "intent": "información",
            "sentiment": "neutral",
        }
        print("  [Extraction] extract(stream_id=%r, %d items) -> %s" % (stream_id, len(items), list(result.keys())))
        return result


# -----------------------------------------------------------------------------
# Ejecución de la llamada simulada
# -----------------------------------------------------------------------------

async def main() -> None:
    print("=" * 60)
    print("Test Orquestador V2 — Llamada simulada con mocks")
    print("=" * 60)

    transport = MockTransport()
    config_port = MockConfigPort()
    stt_port = MockSTTPort()
    llm_port = MockLLMPort()
    tts_port = MockTTSPort()
    persistence_port = MockPersistencePort()
    extraction_port = MockExtractionPort()
    stream_id = "test-stream-001"

    orchestrator = Orchestrator(
        transport=transport,
        stt_port=stt_port,
        llm_port=llm_port,
        tts_port=tts_port,
        config_port=config_port,
        client_type="browser",
        agent_id=1,
        stream_id=stream_id,
        persistence_port=persistence_port,
        extraction_port=extraction_port,
    )

    # 1. Inicio
    print("\n--- 1. orchestrator.start() ---")
    await orchestrator.start()
    print("  OK Config cargada, persistencia create_call si aplica.\n")

    # 2. Primer fragmento de audio (usuario “habla”)
    print("--- 2. orchestrator.process_audio(primer chunk) ---")
    fake_audio_1 = b"\x00\x00" * 8000  # 1 s de “silencio” PCM 16-bit
    await orchestrator.process_audio(fake_audio_1)
    print("  OK Pipeline: STT -> LLM -> TTS -> transport.send_audio.\n")

    # 3. Segundo fragmento (segunda “frase” del usuario)
    print("--- 3. orchestrator.process_audio(segundo chunk) ---")
    fake_audio_2 = b"\x00\x01\x00\xff" * 4000
    await orchestrator.process_audio(fake_audio_2)
    print("  OK Segunda ronda STT -> LLM -> TTS.\n")

    # 4. Cierre
    print("--- 4. orchestrator.stop() ---")
    await orchestrator.stop()
    print("  OK Transcripciones guardadas, extracción, end_call, transport.close.\n")

    # Resumen
    print("=" * 60)
    print("Resumen:")
    print("  - Chunks de audio enviados al cliente: %d" % len(transport.sent_audio_chunks))
    print("  - Total bytes de audio: %d" % sum(transport.sent_audio_chunks))
    print("  - Mensajes JSON (transcripción en vivo): %d" % len(transport.sent_jsons))
    print("  - Transport cerrado: %s" % transport.closed)
    print("=" * 60)
    print("Llamada simulada completada sin errores.")


if __name__ == "__main__":
    asyncio.run(main())
