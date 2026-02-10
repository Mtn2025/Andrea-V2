"""
Orchestrator V2 — Coordinador del flujo de voz.

Carga configuración, construye el pipeline (STT → LLM → TTS) y expone
process_audio(audio_bytes) para cada fragmento de audio del usuario.
Envía el audio de respuesta por AudioTransport.

Política de errores (Fase 1): ante error crítico (config, STT, LLM, TTS) se intenta
enviar mensaje de disculpa por TTS y se cierra la sesión; se lanza CriticalCallError
para que el entry point registre el error y aplique paro global si corresponde.

Persistencia (Fase 2): si se inyecta CallPersistencePort y stream_id, al inicio se
crea el registro de llamada y al stop() se guardan transcripciones (user/assistant)
y se cierra la llamada en BD.

Referencia legacy: app/core/orchestrator_v2.py (idea de config + pipeline + transport).
Docs: docs/POLITICAS_Y_FLUJOS.md, docs/APP_V2_BUILD_LOG.md Pasos 5 y 6.
"""

import logging
import time

from app_v2.domain.ports import (
    AudioTransport,
    CallConfig,
    CallPersistencePort,
    ConfigPort,
    ConfigPortError,
    ExtractionPort,
    LLMMessage,
    LLMPort,
    STTPort,
    TTSPort,
    TTSRequest,
)
from app_v2.domain.value_objects import VoiceConfig
from app_v2.application.errors import CriticalCallError
from app_v2.application.frames import AudioFrame, Frame, TextFrame
from app_v2.application.pipeline import Pipeline
from app_v2.application.processors import LLMProcessor, STTProcessor, TTSProcessor

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orquestador mínimo: configuración, pipeline y envío de audio.
    """

    def __init__(
        self,
        transport: AudioTransport,
        stt_port: STTPort,
        llm_port: LLMPort,
        tts_port: TTSPort,
        config_port: ConfigPort,
        client_type: str = "browser",
        agent_id: int = 1,
        stream_id: str | None = None,
        persistence_port: CallPersistencePort | None = None,
        extraction_port: ExtractionPort | None = None,
    ) -> None:
        self._transport = transport
        self._stt = stt_port
        self._llm = llm_port
        self._tts = tts_port
        self._config_port = config_port
        self._client_type = client_type
        self._agent_id = agent_id
        self._stream_id = stream_id
        self._persistence_port = persistence_port
        self._extraction_port = extraction_port
        self._config: CallConfig | None = None
        self._conversation_history: list[LLMMessage] = []
        self._call_db_id: int | None = None
        self._last_tts_sent_at: float | None = None

    async def start(self) -> None:
        """
        Carga la configuración para la llamada.
        Debe llamarse antes de process_audio.
        En fallo de config cierra el transport y lanza CriticalCallError.
        """
        try:
            self._config = await self._config_port.get_config_for_call(
                self._client_type,
                self._agent_id,
            )
        except ConfigPortError as e:
            logger.error("Config load failed: %s", e)
            await self._transport.close()
            raise CriticalCallError(f"config_load_failed: {e!s}") from e
        except Exception as e:
            logger.error("Unexpected error loading config: %s", e)
            await self._transport.close()
            raise CriticalCallError(f"config_load_failed: {e!s}") from e

        if self._config.system_prompt:
            self._conversation_history = [
                LLMMessage(role="system", content=self._config.system_prompt),
            ]
        else:
            self._conversation_history = []

        if self._persistence_port and self._stream_id:
            self._call_db_id = await self._persistence_port.create_call(
                self._stream_id,
                self._client_type,
            )

    async def _apologize_and_close(self) -> None:
        """
        Intenta enviar mensaje de disculpa por TTS y cierra el transport.
        Si TTS falla, solo cierra. Política de errores Fase 1.
        """
        if self._config and self._config.apology_message.strip():
            try:
                voice = VoiceConfig.from_call_config(self._config)
                params = voice.to_tts_params()
                request = TTSRequest(
                    text=self._config.apology_message.strip(),
                    voice_id=params["voice_id"],
                    language=params["language"],
                    speed=params["speed"],
                    pitch=params["pitch"],
                    volume=params["volume"],
                )
                audio_bytes = await self._tts.synthesize(request)
                if audio_bytes:
                    await self._transport.send_audio(
                        audio_bytes,
                        sample_rate=self._config.sample_rate,
                    )
                    self._last_tts_sent_at = time.time()
            except Exception as e:
                logger.warning("Apology TTS failed, closing anyway: %s", e)
        await self._transport.close()

    async def _emit_transcript_live(self, frame: Frame) -> None:
        """
        Emite transcripción en vivo al panel del simulador (solo browser).
        Información temporal, tipo log; no afecta al historial.
        """
        if self._client_type != "browser":
            return
        if isinstance(frame, TextFrame):
            await self._transport.send_json(
                {"type": "transcript", "role": frame.role, "text": frame.text}
            )

    async def process_audio(self, audio_bytes: bytes) -> None:
        """
        Procesa un bloque de audio del usuario: STT → LLM → TTS y envía el audio resultante.
        Para cliente browser, emite también transcripción en vivo (user/assistant) al panel.
        Ante error crítico: disculpa por TTS, cierre y CriticalCallError.

        Args:
            audio_bytes: Audio del usuario (formato según config: sample_rate, etc.).
        """
        if self._config is None:
            return
        # Protección anti-eco: rechazar audio entrante poco después de enviar TTS
        if self._last_tts_sent_at is not None:
            elapsed = time.time() - self._last_tts_sent_at
            if elapsed < 2.0:
                logger.debug(
                    "Rechazando audio (eco protection: %.2fs desde último TTS)",
                    elapsed,
                )
                return
        try:
            stt_p = STTProcessor(self._stt, self._config)
            llm_p = LLMProcessor(self._llm, self._config, self._conversation_history)
            tts_p = TTSProcessor(self._tts, self._config)
            pipeline = Pipeline([stt_p, llm_p, tts_p])
            initial = AudioFrame(
                data=audio_bytes,
                sample_rate=self._config.sample_rate,
            )
            result = await pipeline.run(initial, on_frame=self._emit_transcript_live)
            if result is not None and isinstance(result, AudioFrame):
                await self._transport.send_audio(
                    result.data,
                    sample_rate=result.sample_rate,
                )
                self._last_tts_sent_at = time.time()
        except CriticalCallError:
            raise
        except Exception as e:
            logger.error("Critical error in process_audio: %s", e)
            await self._apologize_and_close()
            raise CriticalCallError(str(e)) from e

    async def stop(self) -> None:
        """
        Persiste transcripciones y cierra la llamada en BD si hay CallPersistencePort;
        luego cierra el transport.
        """
        if self._persistence_port and self._call_db_id is not None:
            items = [
                (m.role, m.content)
                for m in self._conversation_history
                if m.role in ("user", "assistant")
            ]
            try:
                await self._persistence_port.save_transcripts(self._call_db_id, items)
                if self._extraction_port and self._stream_id and items:
                    extracted = await self._extraction_port.extract(
                        self._stream_id,
                        items,
                    )
                    if extracted:
                        await self._persistence_port.update_call_extraction(
                            self._call_db_id,
                            extracted,
                        )
                await self._persistence_port.end_call(self._call_db_id)
            except Exception as e:
                logger.warning("Persistence on stop failed: %s", e)
        await self._transport.close()
