"""
Ruta WebSocket del Simulador V2.

Monta el orquestador app_v2 (Orchestrator + adapters V2) y el loader de config de app.
Aplica política de errores Fase 1: comprueba paro global antes de aceptar;
registra CriticalCallError y activa paro global si corresponde.

Ruta: /ws/simulator/v2/stream.
Referencia: app/api/routes_simulator.py (legacy).
Documentación: docs/APP_V2_BUILD_LOG.md (Paso 4 y 5), docs/POLITICAS_Y_FLUJOS.md.
"""

import base64
import contextlib
import json
import logging
import uuid

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.api.connection_manager import manager
from app.api.v2_config_loader import load_config_for_call
from app.core.config import settings
from app.core.global_call_policy import (
    is_calls_allowed,
    report_critical_error as report_policy_error,
)
from app.db.database import AsyncSessionLocal
from app.adapters.outbound.extraction.v2_extraction_adapter import V2ExtractionAdapter
from app.adapters.outbound.persistence.v2_call_persistence_adapter import (
    V2CallPersistenceAdapter,
)

from app_v2.adapters import (
    AzureTTSAdapter,
    ConfigAdapter,
    GroqLLMAdapter,
    GroqWhisperSTTAdapter,
    WebSocketTransport,
)
from app_v2.application import Orchestrator
from app_v2.application.errors import CriticalCallError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start")
async def start_simulator_v2_session():
    """Inicia sesión del simulador V2. Conectar después a /ws/simulator/v2/stream."""
    return {"status": "ready", "message": "Connect to /ws/simulator/v2/stream", "version": "v2"}


@router.websocket("/stream")
async def simulator_stream_v2(websocket: WebSocket):
    """
    WebSocket del simulador usando solo orquestador y adapters V2.
    Query param opcional: client_id (si no se envía, se genera un UUID).
    """
    client_id = websocket.query_params.get("client_id") or str(uuid.uuid4())
    logger.info("Simulator V2 connected | ID: %s", client_id)

    if not is_calls_allowed():
        await websocket.close(code=1011, reason="Global call stop active")
        return

    try:
        await manager.connect(client_id, websocket)
    except Exception as e:
        logger.error("Manager connect failed: %s", e)
        return

    config_loader = load_config_for_call
    config_port = ConfigAdapter(loader=config_loader)
    stt_port = GroqWhisperSTTAdapter(
        api_key=settings.GROQ_API_KEY or "",
        model="whisper-large-v3",
    )
    llm_port = GroqLLMAdapter(
        api_key=settings.GROQ_API_KEY or "",
        model=getattr(settings, "GROQ_MODEL", None) or "llama-3.3-70b-versatile",
    )
    tts_port = AzureTTSAdapter(
        api_key=settings.AZURE_SPEECH_KEY or "",
        region=settings.AZURE_SPEECH_REGION or "eastus",
        output_format="pcm_16k",
    )
    transport = WebSocketTransport(websocket)
    persistence = V2CallPersistenceAdapter(session_factory=AsyncSessionLocal)
    extraction = V2ExtractionAdapter()

    orchestrator = Orchestrator(
        transport=transport,
        stt_port=stt_port,
        llm_port=llm_port,
        tts_port=tts_port,
        config_port=config_port,
        client_type="browser",
        agent_id=1,
        stream_id=client_id,
        persistence_port=persistence,
        extraction_port=extraction,
    )
    manager.register_orchestrator(client_id, orchestrator)

    try:
        await orchestrator.start()
    except CriticalCallError as e:
        logger.error("Orchestrator V2 start failed (critical): %s", e.reason)
        report_policy_error(
            reason=e.reason,
            call_id=client_id,
            client_type="browser",
        )
        manager.disconnect(client_id, websocket)
        await websocket.close()
        return
    except Exception as e:
        logger.error("Orchestrator V2 start failed: %s", e)
        manager.disconnect(client_id, websocket)
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            event = msg.get("event")

            if event == "start":
                pass
            elif event == "media":
                payload = msg.get("media", {}).get("payload")
                if payload:
                    try:
                        audio_bytes = base64.b64decode(payload)
                        await orchestrator.process_audio(audio_bytes)
                    except CriticalCallError as e:
                        report_policy_error(
                            reason=e.reason,
                            call_id=client_id,
                            client_type="browser",
                        )
                        break
                    except Exception as e:
                        logger.warning("process_audio failed: %s", e)
            elif event == "stop":
                break
    except WebSocketDisconnect:
        logger.info("Simulator V2 disconnected: %s", client_id)
    except Exception as e:
        logger.error("Simulator V2 WS error: %s", e)
    finally:
        manager.disconnect(client_id, websocket)
        await orchestrator.stop()
        with contextlib.suppress(RuntimeError):
            await websocket.close()
