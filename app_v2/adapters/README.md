# Adaptadores V2

## Responsabilidad

Implementar los **ports** del dominio (`app_v2.domain`) usando proveedores reales (Azure, Groq) o infraestructura (WebSocket, carga de config). Los adapters **no** importan de `app/`; reciben credenciales y dependencias por constructor (inyección).

## Estructura

| Carpeta | Contenido |
|---------|-----------|
| `outbounds/` | STT (Groq Whisper), LLM (Groq), TTS (Azure), Config (loader inyectado). |
| `inbounds/` | WebSocketTransport: implementa AudioTransport sobre FastAPI WebSocket. |

## Contratos implementados

- **ConfigPort**: `ConfigAdapter(loader)` — loader es una función async (client_type, agent_id) -> CallConfig; la implementación real (BD, app) se inyecta desde el entry point.
- **STTPort**: `GroqWhisperSTTAdapter(api_key)` — transcribe_audio vía Groq Whisper (mismo camino que legacy para one-shot).
- **LLMPort**: `GroqLLMAdapter(api_key, model)` — generate_stream vía Groq chat.completions (solo texto en Fase 3).
- **TTSPort**: `AzureTTSAdapter(api_key, region, output_format)` — synthesize vía Azure Speech SDK (SSML, 16kHz PCM para browser).
- **AudioTransport**: `WebSocketTransport(websocket)` — send_audio (base64 JSON), send_json, set_stream_id, close.

## Dependencias externas

- `groq` (AsyncGroq): STT (Whisper) y LLM.
- `azure.cognitiveservices.speech`: TTS.
- `fastapi.WebSocket`: solo en WebSocketTransport.

Ningún import desde `app/`.

## Referencia

- Build Log: docs/APP_V2_BUILD_LOG.md (Paso 3).
