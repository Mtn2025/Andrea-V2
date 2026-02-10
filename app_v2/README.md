# App V2 — Orquestador de voz (core limpio)

## Propósito

Segunda versión del orquestador de voz, construida **desde cero** usando el código legacy (`app/`) únicamente como **referencia**. Objetivos:

- Incluir **solo lo útil** para el flujo objetivo (Simulador → Telnyx/Twilio).
- Conectar **limpiamente** las capas (dominio → aplicación → adapters → entrada).
- Evitar contaminación por reparaciones sobre el legacy.

## Estructura

```
app_v2/
├── README.md                 # Este archivo
├── domain/                   # Capa 1: contratos y tipos (sin implementaciones)
│   ├── README.md
│   ├── ports/
│   ├── models/
│   └── value_objects/
├── application/              # Capa 2 (Fase 2): orquestador, pipeline, frames
├── adapters/                 # Capa 3 (Fase 3): implementaciones de ports
└── entry/                    # Capa 4 (Fase 4): puntos de entrada (WebSocket, etc.)
```

## Documentación obligatoria

- **Cada paso y decisión**: [docs/APP_V2_BUILD_LOG.md](../docs/APP_V2_BUILD_LOG.md).
- **Plan general**: [docs/PLAN_CORE_V2.md](../docs/PLAN_CORE_V2.md).
- **Políticas (flujo de datos, errores)**: [docs/POLITICAS_Y_FLUJOS.md](../docs/POLITICAS_Y_FLUJOS.md).

## Reglas

1. **Ningún módulo en `app_v2/` importa desde `app/`.**
2. Cada paquete tiene su `README.md` con propósito y responsabilidades.
3. Los cambios y decisiones se registran en el Build Log.

## Estado actual

- **Fase 1 (Dominio)**: Completada — ports, modelos, value objects.
- **Fase 2 (Aplicación)**: Completada — frames, pipeline, procesadores, orquestador; tests con mocks pasando.
- **Fase 3 (Adaptadores)**: Completada — ConfigAdapter (loader inyectado), Groq Whisper STT, Groq LLM, Azure TTS, WebSocketTransport; tests de ConfigAdapter y application pasando (4 tests).
- **Fase 4**: Completada — loader en `app/api/v2_config_loader.py`, ruta WebSocket en `app/api/routes_simulator_v2.py` (prefix `/ws/simulator/v2`, endpoint `/stream`). Montada en `app/main.py`. Flujo 100% V2 disponible en `/ws/simulator/v2/stream`.
- **Políticas de error (plan producción Fase 1)**: Completada — detección de error crítico, disculpa por TTS (`CallConfig.apology_message`), cierre, excepción `CriticalCallError`; paro global y notificación en `app/core/global_call_policy`; reanudación vía `POST /admin/reset-global-stop`. Ver `docs/APP_V2_BUILD_LOG.md` Paso 5.
- **Persistencia al cierre (plan producción Fase 2)**: Completada — `CallPersistencePort` (create_call, save_transcripts, end_call); `V2CallPersistenceAdapter` en app; orquestador con stream_id y persistence_port opcionales; sesiones simulador V2 se registran en la misma BD/Historial que el dashboard. Ver `docs/APP_V2_BUILD_LOG.md` Paso 6.
- **UI V2 (plan producción Fase 3)**: Completada — Ruta GET /dashboard/v2, template `dashboard_v2.html` (copia con `window.USE_V2_SIMULATOR = true`), simulador en esa página usa `/ws/simulator/v2/stream`. Config e historial comparten contexto y BD con el backend V2. Ver `docs/APP_V2_BUILD_LOG.md` Paso 7.
- **Telefonía V2 (plan producción Fase 4)**: Completada — Transport `V2TelephonyTransport` en `app/adapters/telephony/v2_telephony_transport.py`; WebSocket `/api/v1/ws/media-stream` en `app/api/routes_telephony.py` usa Orchestrator V2 (STT/LLM/TTS, persistencia, política de errores). TTS en telephony: `mulaw_8k`. Ver `docs/APP_V2_BUILD_LOG.md` Paso 8.
- **Paridad extracción (plan producción Fase 5)**: Completada — `ExtractionPort` y `update_call_extraction` en CallPersistencePort; `V2ExtractionAdapter` usa extraction_service; orquestador en stop() ejecuta extracción y actualiza Call.extracted_data antes de end_call. Simulador y telephony V2 inyectan extraction_port. Ver `docs/APP_V2_BUILD_LOG.md` Paso 9.
- **Preparación para producción (plan producción Fase 6)**: Completada — GET /health (liveness), `docs/VARIABLES_ENTORNO.md`, `docs/OPERACION.md`, actualización COOLIFY_DEPLOY y DEPLOY_CHECKLIST. Ver `docs/APP_V2_BUILD_LOG.md` Paso 10.
