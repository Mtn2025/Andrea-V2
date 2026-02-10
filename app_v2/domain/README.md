# Dominio V2

## Responsabilidad

Definir **contratos (ports)** y **tipos de dominio** (modelos, value objects) para el flujo de voz. Esta capa **no** contiene implementaciones ni dependencias de infraestructura (`app/`, BD, HTTP, WebSocket).

## Contenido

| Carpeta | Contenido |
|---------|-----------|
| `ports/` | Interfaces (ABC) que deben implementar los adapters: AudioTransport, STTPort, LLMPort, TTSPort, ConfigPort, CallPersistencePort. Incluye DTOs/params asociados (STTConfig, TTSRequest, CallConfig, etc.). CallPersistencePort (Fase 2): create_call, save_transcripts, end_call para Historial. |
| `models/` | Modelos de dominio usados en los contratos: LLMChunk, etc. (requests/responses que no son responsabilidad de un solo port). |
| `value_objects/` | Objetos inmutables y validados: VoiceConfig para TTS. |

## Qué no incluye

- Casos de uso de aplicación (irán en `application/`).
- FSM, tool calling, barge-in (se añadirán en fases posteriores cuando el flujo básico esté estable).
- Cualquier import desde `app/`.

## Referencia

- Build Log: docs/APP_V2_BUILD_LOG.md (Paso 1).
- Plan: docs/PLAN_CORE_V2.md.
