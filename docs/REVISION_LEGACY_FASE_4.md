# Revisión legacy — Fase 4: Telefonía (Telnyx / Twilio)

**Objetivo de la revisión**: Identificar el flujo de telephony (webhooks, WebSocket, formato de audio, transport) para migrar al core V2 sin cambiar URLs ni comportamiento externo; solo el motor interno pasa a Orchestrator V2.

**Fecha de la revisión**: 2026-02-09  
**Fase del plan**: Fase 4 — Migración de Telefonía (Telnyx/Twilio) al core V2.

---

## 1. Ámbito revisado

| Ruta | Rol |
|------|-----|
| `app/api/routes_telephony.py` | Router con prefix API_V1_STR (/api/v1). Twilio: GET/POST /twilio/incoming-call (TwiML con Stream url wss://host/api/v1/ws/media-stream). Telnyx: POST /telnyx/call-control (call.initiated → answer, call.answered → streaming_start con stream_url a /api/v1/ws/media-stream?client=telnyx&call_control_id=...). WebSocket /ws/media-stream (client, call_control_id, client_state); usa TelephonyTransport, get_voice_ports(audio_mode=client), VoiceOrchestratorV2 legacy. |
| `app/adapters/telephony/transport.py` | TelephonyTransport(websocket, protocol="twilio"|"telnyx"): send_audio (base64, event "media", streamSid/stream_id), send_json, set_stream_id, handle_event (VAD Telnyx), close() vacío. Implementa app.domain.ports.AudioTransport. |
| `app/core/voice_ports.py` | get_voice_ports(audio_mode): devuelve VoicePorts (STT, LLM, TTS, config_repo, call_repo, transcript_repo, tools) para browser/twilio/telnyx. |
| `app/main.py` | include_router(routes_telephony, prefix=settings.API_V1_STR) → ruta final /api/v1/ws/media-stream. |

---

## 2. Hallazgos

### 2.1 URL del WebSocket y webhooks

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `routes_telephony.py` | TwiML y Telnyx stream_url apuntan a `wss://{host}/api/v1/ws/media-stream` (con query client=telnyx&call_control_id=... para Telnyx). | No cambiar URL; el mismo endpoint debe atender con el orquestador V2. No crear /api/v1/ws/media-stream-v2. |

### 2.2 Eventos del WebSocket (entrada)

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `routes_telephony.py` L192-218 | event "connected" (ignorado), "start" (stream_sid → orchestrator.stream_id, transport.set_stream_id), "media" (msg["media"]["payload"] base64 → process_audio(payload) legacy), "stop" (break), "client_interruption" (pass). mark "speech_ended" → is_bot_speaking = False. | V2: payload es base64; decodificar a bytes y llamar orchestrator.process_audio(audio_bytes). stream_id se pasa al orquestador como stream_id=client_id; al recibir "start" se puede actualizar el transport.set_stream_id(stream_sid) para envío de audio. |

### 2.3 TelephonyTransport y formato de salida

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/adapters/telephony/transport.py` | send_audio: Twilio → event "media", streamSid, media.payload (b64). Telnyx → event "media", stream_id, media.payload, media.track "inbound_track". close() no cierra el socket. | Implementar un adapter en app que implemente app_v2.domain.ports.AudioTransport: misma lógica de mensaje; close() debe cerrar el WebSocket. |

### 2.4 Formato de audio (telephony)

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/core/voice_ports.py`, `v2_config_loader` | audio_mode twilio/telnyx → sample_rate 8000; TTS para telephony suele ser mulaw 8kHz. | AzureTTSAdapter V2 ya tiene output_format "mulaw_8k"; usarlo cuando client_type sea twilio o telnyx. load_config_for_call(client_type) ya devuelve sample_rate=8000 para no-browser. |

### 2.5 Parámetros del WebSocket

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `routes_telephony.py` L141 | telephony_media_stream(websocket, client="twilio", call_control_id=None, client_state=None). client_id = call_control_id or uuid. | client es "twilio" o "telnyx"; usarlo como client_type para load_config_for_call y para el transport. client_id como stream_id para persistencia. |

---

## 3. Conclusiones

### 3.1 Estrategia

- **Misma ruta, mismo URL**: El handler del WebSocket /api/v1/ws/media-stream se cambia para instanciar Orchestrator V2 (app_v2), ConfigAdapter(load_config_for_call) con client_type=client (twilio|telnyx), GroqWhisperSTTAdapter, GroqLLMAdapter, AzureTTSAdapter(..., output_format="mulaw_8k"), y un **transport que implemente app_v2.domain.ports.AudioTransport** con la misma lógica que TelephonyTransport (Twilio/Telnyx) y close() que cierre el socket.
- **Transport V2 en app**: Nuevo módulo (ej. app/adapters/telephony/v2_telephony_transport.py) que implemente AudioTransport de app_v2: send_audio (base64, event media, protocol-specific), send_json, set_stream_id, close (websocket.close()). Sin dependencia de app_v2 más allá del port (import del ABC).
- **Persistencia y política**: Igual que simulador V2: V2CallPersistenceAdapter, stream_id=client_id, is_calls_allowed(), report_critical_error en start y en media.
- **Webhooks**: Sin cambios; TwiML y Telnyx call control siguen igual; solo cambia el código que ejecuta el WebSocket.

### 3.2 Qué no se replica

- handle_event (VAD) del legacy transport: opcional para una fase posterior; el orquestador V2 no lo usa. Se puede añadir como método no-interface en el adapter si se quiere conservar logging.
- tools, FSM, greeting: ya no están en el orquestador V2; fuera de alcance de Fase 4.

### 3.3 Criterio de cierre

- Una llamada entrante por Telnyx (y otra por Twilio) se atiende con el orquestador V2, audio mulaw 8k, y al finalizar se persiste en Historial y se aplican políticas de error (disculpa, paro global si aplica).

---

## 4. Referencias cruzadas

- Plan: `docs/PLAN_TRABAJO_PRODUCCION.md` — Fase 4.
- Build Log: `docs/APP_V2_BUILD_LOG.md` — Paso 8 (por crear).
- Simulador V2: `app/api/routes_simulator_v2.py` (patrón de integración).

---

*Revisión legacy cerrada. Próximo paso: implementar V2TelephonyTransport en app, cambiar handler de /ws/media-stream a Orchestrator V2; registrar en Build Log.*
