# App V2 — Registro de construcción (Build Log)

**Objetivo**: Construir el orquestador V2 desde cero; el código legacy (`app/`) es **solo referencia**.  
**Principio**: Documentar cada paso, cada decisión y cada archivo para saber en todo momento qué ajustar y dónde.

---

## Convenciones del Build Log

- **Paso**: Fase o bloque de trabajo con fecha.
- **Decisión**: Qué se decidió y por qué.
- **Archivos**: Qué se creó o modificó.
- **Referencia legacy**: Qué se tomó como idea (sin copiar); qué se omitió.

### Convención: variables de entorno (Coolify / Docker)

- Despliegue: Docker Compose, Coolify; código por **git push main**. Las variables de entorno **no se comparten** entre entornos.
- **No hardcodear** en código ningún valor que deba venir de env (API keys, regiones, modelos, URLs, secretos). Usar siempre `app/core/config.py` (Settings / pydantic-settings); los defaults en Settings son solo fallback cuando la variable no está definida.
- Ver `docs/PLAN_TRABAJO_PRODUCCION.md` § Contexto de despliegue.

---

## Paso 1 — Estructura raíz y dominio V2 (2026-02-09)

### Decisión 1.1 — Ubicación de V2

- **Decisión**: Crear el árbol V2 bajo `app_v2/` en la raíz del proyecto (hermano de `app/`).
- **Motivo**: Evitar mezcla con legacy; imports serán `from app_v2.domain...` sin tocar `app`.
- **Referencia legacy**: Ninguna; estructura nueva.

### Decisión 1.2 — Documentación obligatoria

- **Decisión**: Cada paquete V2 tendrá un `README.md` que describa su propósito, responsabilidades y qué no hace. Cada módulo tendrá docstring de módulo y decisiones clave en este Build Log.
- **Motivo**: Saber siempre qué hace cada pieza y por qué existe.

### Decisión 1.3 — Contratos del dominio (ports)

- **Decisión**: Los ports del dominio V2 serán **mínimos** para el primer flujo: Simulador (navegador), flujo audio → STT → LLM → TTS → audio.
- **Ports incluidos**:
  - `AudioTransport`: envío de audio y JSON al cliente; cierre.
  - `STTPort`: `transcribe_audio(audio_bytes, config) -> str` (síncrono al uso para el primer flujo).
  - `LLMPort`: `generate_stream(request) -> AsyncIterator[LLMChunk]`; modelos `LLMMessage`, `LLMRequest`, `LLMChunk` (solo texto en el primer slice).
  - `TTSPort`: `synthesize(request) -> bytes`; modelo `TTSRequest`.
  - `ConfigPort`: `get_config_for_call(client_type: str, agent_id: int = 1) -> CallConfig`; retorno es DTO de dominio, nunca ORM.
- **Referencia legacy**: `app/domain/ports/*` como idea de nombres y métodos; se simplifica (sin STTRecognizer streaming en Fase 1, sin tools en LLM en Fase 1).

### Decisión 1.4 — Modelos y value objects

- **Decisión**: Modelos en `app_v2/domain/models/`: solo los necesarios para los contratos (LLMMessage, LLMRequest, LLMChunk, TTSRequest, CallConfig). Value objects en `app_v2/domain/value_objects/`: `VoiceConfig` (inmutable) para TTS.
- **Motivo**: Un solo flujo; no incorporar tool calling ni FSM hasta capas siguientes.
- **Referencia legacy**: `app/domain/models/llm_models.py`, `tool_models.py`, `value_objects/voice_config.py`; se omiten tools y se mantiene tipado estricto (`| None` donde aplique).

### Decisión 1.5 — Sin dependencias de `app`

- **Decisión**: Ningún archivo bajo `app_v2/` importa desde `app/`.
- **Motivo**: V2 es independiente; la migración se hace por entrada (rutas) que instancian V2, no por mezcla de módulos.

---

## Archivos creados en Paso 1

| Ruta | Propósito |
|------|-----------|
| `app_v2/README.md` | Índice y guía del proyecto V2; enlace a este Build Log. |
| `app_v2/__init__.py` | Paquete raíz V2; sin exports de dominio (evitar import circular). |
| `app_v2/domain/README.md` | Capa dominio: responsabilidades, ports, modelos, qué no incluye. |
| `app_v2/domain/__init__.py` | Export público del dominio V2 (ports, models, value_objects). |
| `app_v2/domain/ports/__init__.py` | Export de todos los ports y tipos asociados. |
| `app_v2/domain/ports/audio_transport.py` | Interface AudioTransport (4 métodos). |
| `app_v2/domain/ports/stt_port.py` | Interface STTPort + STTConfig (transcribe_audio). |
| `app_v2/domain/ports/llm_port.py` | Interface LLMPort + LLMMessage, LLMRequest (generate_stream). |
| `app_v2/domain/ports/tts_port.py` | Interface TTSPort + TTSRequest (synthesize). |
| `app_v2/domain/ports/config_port.py` | Interface ConfigPort + CallConfig (DTO) + ConfigPortError. |
| `app_v2/domain/models/__init__.py` | Export de modelos (LLMChunk). |
| `app_v2/domain/models/llm_models.py` | LLMChunk (text, finish_reason; Fase 1 solo texto). |
| `app_v2/domain/value_objects/__init__.py` | Export de value objects. |
| `app_v2/domain/value_objects/voice_config.py` | VoiceConfig inmutable; from_call_config(CallConfig); to_tts_params(). |

### Decisión 1.6 — VoiceConfig y CallConfig

- **Decisión**: VoiceConfig.from_call_config(config: CallConfig) construye el value object desde el DTO; se usa TYPE_CHECKING para importar CallConfig solo en type-checking y evitar import circular en runtime.
- **Verificación**: `python -c "from app_v2.domain import ...; VoiceConfig.from_call_config(CallConfig(...))"` ejecutado correctamente.

---

## Índice rápido de archivos V2 (Paso 1)

```
app_v2/
├── README.md
├── __init__.py
└── domain/
    ├── README.md
    ├── __init__.py
    ├── ports/
    │   ├── __init__.py
    │   ├── audio_transport.py   # AudioTransport
    │   ├── stt_port.py          # STTPort, STTConfig
    │   ├── llm_port.py          # LLMPort, LLMMessage, LLMRequest
    │   ├── tts_port.py          # TTSPort, TTSRequest
    │   └── config_port.py       # ConfigPort, CallConfig, ConfigPortError
    ├── models/
    │   ├── __init__.py
    │   └── llm_models.py        # LLMChunk
    └── value_objects/
        ├── __init__.py
        └── voice_config.py      # VoiceConfig
```

**Uso**: `from app_v2.domain import CallConfig, ConfigPort, LLMPort, STTPort, TTSPort, AudioTransport, VoiceConfig, LLMChunk, LLMMessage, LLMRequest, TTSRequest, STTConfig`

---

## Paso 2 — Capa aplicación V2 (2026-02-09)

### Decisión 2.1 — Frames mínimos

- **Decisión**: Solo Frame (base con trace_id, timestamp), AudioFrame (data, sample_rate, channels), TextFrame (text, role). Sin SystemFrame, ControlFrame ni prioridades.
- **Motivo**: Flujo lineal; prioridades y control en fases posteriores.
- **Referencia legacy**: app/core/frames.py (idea de Frame con trace_id).

### Decisión 2.2 — Dataclasses con kw_only

- **Decisión**: Frame, AudioFrame y TextFrame son @dataclass(kw_only=True) para evitar "non-default argument follows default" en herencia (campos base con default, hijos con data/text obligatorios).
- **Verificación**: Tests pasan; construcción con keyword args en todos los procesadores.

### Decisión 2.3 — Processor y pipeline secuencial

- **Decisión**: Processor (ABC) con async def process(frame) -> Frame | None. Pipeline(processors) con async def run(frame) que ejecuta cada procesador en orden; si uno devuelve None, se detiene.
- **Motivo**: Sin cola ni backpressure en Fase 2; un solo frame recorre la cadena.
- **Referencia legacy**: app/core/processor.py, pipeline.py (idea de cadena).

### Decisión 2.4 — Procesadores STT, LLM, TTS

- **Decisión**: STTProcessor(AudioFrame → TextFrame user), LLMProcessor(TextFrame user → TextFrame assistant; mantiene conversation_history inyectada), TTSProcessor(TextFrame assistant → AudioFrame). Cada uno recibe CallConfig y el port correspondiente.
- **Motivo**: History en orquestador; se inyecta en LLMProcessor para mantener contexto entre turnos.
- **Referencia legacy**: app/processors/logic/stt.py, llm.py, tts.py (idea de uso de ports).

### Decisión 2.5 — Orchestrator sin FSM ni control channel

- **Decisión**: Orchestrator.start() carga CallConfig; process_audio(audio_bytes) construye pipeline (STT→LLM→TTS), ejecuta con AudioFrame(audio_bytes), envía resultado por transport.send_audio(); stop() cierra transport. Sin FSM, sin greeting inicial, sin control channel.
- **Motivo**: Primer flujo funcional; FSM e interrupt en fases posteriores.
- **Referencia legacy**: app/core/orchestrator_v2.py (idea de config + pipeline + transport).

### Decisión 2.6 — Mocks y tests

- **Decisión**: verification_mocks.py en application/ con MockAudioTransport, MockSTTPort, MockLLMPort, MockTTSPort, MockConfigPort para verificación sin proveedores reales. Tests en tests/test_app_v2_application.py (orchestrator process_audio envía audio, start carga config).
- **Verificación**: pytest tests/test_app_v2_application.py — 2 passed.

---

## Archivos creados en Paso 2

| Ruta | Propósito |
|------|-----------|
| `app_v2/application/README.md` | Responsabilidad de la capa, flujo mínimo, qué no incluye. |
| `app_v2/application/__init__.py` | Export Frame, AudioFrame, TextFrame, Pipeline, Processor, Orchestrator. |
| `app_v2/application/frames.py` | Frame, AudioFrame, TextFrame (kw_only). |
| `app_v2/application/processor.py` | Processor (ABC), process(frame) -> Frame \| None. |
| `app_v2/application/processors/__init__.py` | Export STTProcessor, LLMProcessor, TTSProcessor. |
| `app_v2/application/processors/stt_processor.py` | AudioFrame → TextFrame(user) vía STTPort. |
| `app_v2/application/processors/llm_processor.py` | TextFrame(user) → TextFrame(assistant) vía LLMPort; history inyectada. |
| `app_v2/application/processors/tts_processor.py` | TextFrame(assistant) → AudioFrame vía TTSPort + VoiceConfig. |
| `app_v2/application/pipeline.py` | Pipeline(processors), run(frame) secuencial. |
| `app_v2/application/orchestrator.py` | Orchestrator: start, process_audio, stop; construye pipeline por turno. |
| `app_v2/application/verification_mocks.py` | Mocks de los 5 ports para tests/verificación. |
| `tests/test_app_v2_application.py` | Tests: process_audio envía audio, start carga config. |

---

## Índice rápido de archivos V2 (tras Paso 2)

```
app_v2/
├── README.md
├── __init__.py
├── domain/
│   ├── README.md
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── audio_transport.py
│   │   ├── stt_port.py
│   │   ├── llm_port.py
│   │   ├── tts_port.py
│   │   └── config_port.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── llm_models.py
│   └── value_objects/
│       ├── __init__.py
│       └── voice_config.py
└── application/
    ├── README.md
    ├── __init__.py
    ├── frames.py
    ├── processor.py
    ├── pipeline.py
    ├── orchestrator.py
    ├── verification_mocks.py
    └── processors/
        ├── __init__.py
        ├── stt_processor.py
        ├── llm_processor.py
        └── tts_processor.py
```

**Tests**: `pytest tests/test_app_v2_application.py -v`

---

## Paso 3 — Adaptadores V2 (2026-02-09)

### Decisión 3.1 — Config sin dependencia de app

- **Decisión**: ConfigPort se implementa con **ConfigAdapter(loader)** donde `loader` es una función async `(client_type, agent_id) -> CallConfig` inyectada desde el entry point. La implementación real (BD, get_profile, overlays) vive en `app/` o en el punto de montaje; app_v2 no importa app.
- **Motivo**: Mantener app_v2 libre de app.db y app.services; el puente se hace por inyección.
- **Referencia legacy**: app/adapters/outbound/repositories/sqlalchemy_config_repository.py, orchestrator_v2._load_config.

### Decisión 3.2 — STT con Groq Whisper

- **Decisión**: STTPort implementado por **GroqWhisperSTTAdapter(api_key, model)**. Transcripción one-shot (transcribe_audio). No se usa Azure STT en Fase 3 para reducir complejidad; el legacy ya usa Groq Whisper para transcribe_audio.
- **Referencia legacy**: app/adapters/outbound/stt/azure_stt_adapter.py (método transcribe_audio que llama a Groq).

### Decisión 3.3 — LLM con Groq

- **Decisión**: LLMPort implementado por **GroqLLMAdapter(api_key, model)**. generate_stream con chat.completions (solo texto; sin tools). Sin circuit breaker ni decoradores de latencia en V2 por ahora.
- **Referencia legacy**: app/adapters/outbound/llm/groq_llm_adapter.py.

### Decisión 3.4 — TTS con Azure

- **Decisión**: TTSPort implementado por **AzureTTSAdapter(api_key, region, output_format)**. synthesize construye SSML y usa Speech SDK (speak_ssml_async); salida a archivo temporal y lectura de bytes para compatibilidad multiplataforma. output_format: "pcm_16k" (browser) o "mulaw_8k" (telephony).
- **Referencia legacy**: app/adapters/outbound/tts/azure_tts_adapter.py. Corrección: cierre de tag en _build_ssml (xml:lang="{request.language}").

### Decisión 3.5 — Transport WebSocket

- **Decisión**: AudioTransport implementado por **WebSocketTransport(websocket)**. send_audio envía JSON { type: "audio", data: "<base64>" }; send_json envía JSON; close cierra el WebSocket. Tipo del websocket: Any (típicamente fastapi.WebSocket).
- **Referencia legacy**: app/adapters/simulator/transport.py (SimulatorTransport).

### Decisión 3.6 — Sin imports de app

- **Decisión**: Ningún archivo en app_v2/adapters importa desde app/. Credenciales y loader se reciben por constructor.
- **Verificación**: tests/test_app_v2_adapters.py (ConfigAdapter con loader inyectado) y tests/test_app_v2_application.py siguen pasando (4 tests en total).

---

## Archivos creados en Paso 3

| Ruta | Propósito |
|------|-----------|
| `app_v2/adapters/README.md` | Responsabilidad de adapters, contratos, dependencias externas. |
| `app_v2/adapters/__init__.py` | Export ConfigAdapter, GroqWhisperSTTAdapter, GroqLLMAdapter, AzureTTSAdapter, WebSocketTransport. |
| `app_v2/adapters/outbounds/__init__.py` | Export de outbounds. |
| `app_v2/adapters/outbounds/config_adapter.py` | ConfigAdapter(loader) implementa ConfigPort. |
| `app_v2/adapters/outbounds/stt_groq_adapter.py` | GroqWhisperSTTAdapter(api_key, model); transcribe_audio vía Whisper. |
| `app_v2/adapters/outbounds/llm_groq_adapter.py` | GroqLLMAdapter(api_key, model); generate_stream. |
| `app_v2/adapters/outbounds/tts_azure_adapter.py` | AzureTTSAdapter(api_key, region, output_format); synthesize vía SSML + archivo temporal. |
| `app_v2/adapters/inbounds/__init__.py` | Export WebSocketTransport. |
| `app_v2/adapters/inbounds/websocket_transport.py` | WebSocketTransport(websocket) implementa AudioTransport. |
| `tests/test_app_v2_adapters.py` | Tests ConfigAdapter (loader OK, loader failure → ConfigPortError). |

---

## Índice rápido de archivos V2 (tras Paso 3)

```
app_v2/
├── README.md
├── __init__.py
├── domain/
│   ├── README.md
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── audio_transport.py
│   │   ├── stt_port.py
│   │   ├── llm_port.py
│   │   ├── tts_port.py
│   │   └── config_port.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── llm_models.py
│   └── value_objects/
│       ├── __init__.py
│       └── voice_config.py
├── application/
│   ├── README.md
│   ├── __init__.py
│   ├── frames.py
│   ├── processor.py
│   ├── pipeline.py
│   ├── orchestrator.py
│   ├── verification_mocks.py
│   └── processors/
│       ├── __init__.py
│       ├── stt_processor.py
│       ├── llm_processor.py
│       └── tts_processor.py
└── adapters/
    ├── README.md
    ├── __init__.py
    ├── outbounds/
    │   ├── __init__.py
    │   ├── config_adapter.py
    │   ├── stt_groq_adapter.py
    │   ├── llm_groq_adapter.py
    │   └── tts_azure_adapter.py
    └── inbounds/
        ├── __init__.py
        └── websocket_transport.py
```

**Tests**: `pytest tests/test_app_v2_application.py tests/test_app_v2_adapters.py -v` (4 tests)

---

## Paso 4 — Entrada WebSocket Simulador V2 (2026-02-09)

### Decisión 4.1 — Loader de config en app (puente app → CallConfig)

- **Decisión**: El loader que obtiene CallConfig desde BD vive en `app/`: `app/api/v2_config_loader.py`. Usa AsyncSessionLocal, db_service.get_agent_config, orm_config.get_profile(client_type), apply_client_overlay sobre un objeto mutable y mapea a CallConfig con `_mutable_to_call_config`. Así app_v2 no importa app; el puente es solo app → app_v2.
- **Motivo**: Respetar la regla "app_v2 no importa app"; la configuración real (BD, perfiles, overlay) sigue en app.
- **Referencia legacy**: app/core/orchestrator_v2._load_config, app/domain/config_logic (apply_client_overlay).

### Decisión 4.2 — CallConfig desde mutable tras overlay

- **Decisión**: Tras apply_client_overlay(mutable, client_type), se construye CallConfig leyendo atributos del objeto mutable con getattr y valores por defecto. No se reconstruye ProfileConfigSchema; así voice_pacing_ms y silence_timeout_ms (que el overlay puede modificar) quedan correctamente aplicados.
- **Motivo**: apply_client_overlay modifica el objeto mutable; construir CallConfig desde ese objeto evita desalineación.

### Decisión 4.3 — Ruta WebSocket V2

- **Decisión**: Nueva ruta en `app/api/routes_simulator_v2.py`: prefix `/ws/simulator/v2`, endpoint WebSocket `/stream`. Mismo protocolo de mensajes que el simulador legacy: evento `media` con `media.payload` en base64; se decodifica a bytes y se pasa a orchestrator.process_audio(audio_bytes). Eventos `start` y `stop`; client_id opcional por query param (si no se envía, se genera UUID).
- **Motivo**: Punto de entrada único para probar el flujo 100% V2 (Orchestrator + adapters V2 + loader desde app).
- **Referencia legacy**: app/api/routes_simulator.py (eventos y formato de mensajes).

### Decisión 4.4 — Instanciación en la ruta

- **Decisión**: En la ruta se instancian ConfigAdapter(loader=load_config_for_call), GroqWhisperSTTAdapter(settings.GROQ_API_KEY), GroqLLMAdapter(settings.GROQ_API_KEY), AzureTTSAdapter(settings.AZURE_SPEECH_KEY, settings.AZURE_SPEECH_REGION, "pcm_16k"), WebSocketTransport(websocket) y Orchestrator con client_type="browser", agent_id=1. Se usa connection_manager (manager) para connect, register_orchestrator y disconnect igual que el simulador legacy.
- **Motivo**: Misma integración con el manager; credenciales desde settings en app.

---

## Archivos creados/modificados en Paso 4

| Ruta | Propósito |
|------|-----------|
| `app/api/v2_config_loader.py` | load_config_for_call(client_type, agent_id); _mutable_to_call_config; BD + perfil + overlay → CallConfig. |
| `app/api/routes_simulator_v2.py` | Router con POST /start y WebSocket /stream; orquestador V2 + adapters; eventos media (base64→bytes), start, stop. |
| `app/main.py` | Import routes_simulator_v2; include_router(routes_simulator_v2.router, prefix="/ws/simulator/v2", tags=["Simulator V2"]). |

---

## Índice rápido de archivos V2 (tras Paso 4)

- **Entrada (en app/)**: `app/api/v2_config_loader.py`, `app/api/routes_simulator_v2.py`. Ruta montada: **/ws/simulator/v2/stream** (WebSocket), **/ws/simulator/v2/start** (POST).
- El resto del árbol app_v2/ no cambia; ver índice tras Paso 3.

**Verificación**: Tests `test_app_v2_application.py` y `test_app_v2_adapters.py` siguen pasando (4 tests). Para probar en vivo: conectar el frontend del simulador a `ws://.../ws/simulator/v2/stream` (y opcionalmente `?client_id=...`).

---

## Paso 5 — Políticas de error en el core V2 (Fase 1 del plan de producción)

**Revisión legacy**: `docs/REVISION_LEGACY_FASE_1.md`. Referencia: `app/core/control_channel.py`, `app/core/orchestrator_v2.py`, `docs/POLITICAS_Y_FLUJOS.md`.

### Decisión 5.1 — Excepción CriticalCallError

- **Decisión**: Nueva excepción en `app_v2/application/errors.py`: `CriticalCallError(reason, call_id=None)`. El orquestador la lanza tras fallo de config (en start) o tras error en pipeline (en process_audio) después de intentar disculpa y cierre. El entry point (ruta) la captura y delega en la política global (reportar error, paro global si umbral).
- **Motivo**: app_v2 no importa app; el puente es por excepción y manejo en la ruta. Trazabilidad: reason y call_id para logs y notificación.

### Decisión 5.2 — Disculpa y cierre en el orquestador

- **Decisión**: En `start()`: ante ConfigPortError o Exception al cargar config, se cierra el transport y se lanza CriticalCallError. En `process_audio()`: cualquier excepción (salvo CriticalCallError) se considera error crítico; se llama a `_apologize_and_close()` (texto desde `CallConfig.apology_message`, síntesis por TTSPort, envío por transport, luego close) y se lanza CriticalCallError. Si la disculpa por TTS falla, solo se cierra.
- **Motivo**: Cumplir política: disculpa breve + cierre controlado. CallConfig.apology_message con valor por defecto; configurable desde perfil/loader en app.

### Decisión 5.3 — CallConfig.apology_message

- **Decisión**: Campo opcional `apology_message: str` en CallConfig (valor por defecto: "Lo sentimos, hemos tenido un problema. La llamada terminará."). En `v2_config_loader._mutable_to_call_config` se mapea desde perfil si existe; si no, se usa el valor por defecto.
- **Motivo**: Permitir i18n o mensaje por perfil sin tocar app_v2; el loader en app puede leer apology_message del perfil cuando exista.

### Decisión 5.4 — Paro global y notificación (en app)

- **Decisión**: Módulo `app/core/global_call_policy.py`: estado en memoria (`_calls_allowed`, `_error_timestamps`). Ventana de errores configurable por env: `GLOBAL_STOP_MAX_ERRORS_IN_WINDOW` (default 3), `GLOBAL_STOP_WINDOW_SECONDS` (default 60). `report_critical_error(reason, call_id, client_type)`: log estructurado, actualiza ventana; si count >= umbral, activa paro global y llama a `_notify_admin` (log + POST opcional a `ADMIN_NOTIFICATION_WEBHOOK_URL`). `is_calls_allowed()` para que las rutas comprueben antes de aceptar. `reset_global_stop()` para reanudar. Endpoint admin: `POST /admin/reset-global-stop` (protegido por API key).
- **Motivo**: Política "si persiste → paro global + notificación". Estado en app para no acoplar app_v2 a Redis; extensible después a Redis si se requiere.

### Decisión 5.5 — Integración en la ruta simulador V2

- **Decisión**: En `routes_simulator_v2`: antes de crear orquestador, si no `is_calls_allowed()`, se cierra el WebSocket con code 1011 y return. Tras `orchestrator.start()` se captura CriticalCallError y se llama a `report_critical_error` antes de disconnect. En el loop de eventos "media", al capturar CriticalCallError se llama a `report_critical_error` y se sale del loop (finally hace disconnect y stop).
- **Motivo**: Una sola fuente de verdad para política global; la ruta solo delega.

---

## Archivos creados/modificados en Paso 5

| Ruta | Propósito |
|------|-----------|
| `docs/CONVENCIONES_DOCUMENTACION.md` | Estándar de documentación: principios, estructura por tipo, redacción, checklist. |
| `docs/REVISION_LEGACY_FASE_1.md` | Revisión legacy para Fase 1: control channel, orquestador, políticas; hallazgos y conclusiones. |
| `app_v2/application/errors.py` | Excepción CriticalCallError(reason, call_id). |
| `app_v2/domain/ports/config_port.py` | Campo CallConfig.apology_message (default). |
| `app_v2/application/orchestrator.py` | start() con try/except y CriticalCallError; _apologize_and_close(); process_audio() con try/except, disculpa y CriticalCallError. |
| `app/api/v2_config_loader.py` | Mapeo apology_message en _mutable_to_call_config. |
| `app/core/global_call_policy.py` | Estado paro global, report_critical_error, is_calls_allowed, reset_global_stop, _notify_admin (log + webhook). |
| `app/api/routes_simulator_v2.py` | Comprobación is_calls_allowed; manejo CriticalCallError en start y en media; report_critical_error. |
| `app/api/routes_admin.py` | POST /admin/reset-global-stop (verify_api_key). |
| `docs/POLITICAS_Y_FLUJOS.md` | Actualización §2 estado en código V2. |

---

## Paso 6 — Persistencia al cierre de llamada (Historial) en V2 (Fase 2 del plan de producción)

**Revisión legacy**: `docs/REVISION_LEGACY_FASE_2.md`. Referencia: call_repository_port, transcript_repository_port, sqlalchemy_*_repository, db_service, orchestrator_v2 (create_call, _handle_transcript, stop con end_call).

### Decisión 6.1 — Port de persistencia en app_v2

- **Decisión**: Nuevo port `CallPersistencePort` en `app_v2/domain/ports/call_persistence_port.py`: `create_call(stream_id, client_type) -> int | None`, `save_transcripts(call_id, items: list[tuple[str, str]])`, `end_call(call_id)`. Sin dependencias de app; el adapter en app implementa con db_service.
- **Motivo**: Mantener app_v2 sin importar app; el entry point inyecta el adapter que escribe en la misma BD que el dashboard.

### Decisión 6.2 — Adapter en app

- **Decisión**: `app/adapters/outbound/persistence/v2_call_persistence_adapter.py`: `V2CallPersistenceAdapter(session_factory)`. create_call → db_service.create_call; save_transcripts → bucle db_service.log_transcript(call_db_id=call_id); end_call → db_service.end_call. Mismas tablas calls y transcripts.
- **Motivo**: Reutilizar db_service y esquema existente; Historial del dashboard muestra todas las llamadas (legacy y V2).

### Decisión 6.3 — Integración en orquestador

- **Decisión**: Orquestador acepta opcionales `stream_id` y `persistence_port`. En start(): si ambos presentes, `create_call(stream_id, client_type)` y guarda `_call_db_id`. En stop(): si persistence y call_id, convierte `_conversation_history` a lista (role, content) filtrando solo "user" y "assistant", llama `save_transcripts` y `end_call`, luego cierra transport.
- **Motivo**: Transcripciones al cierre en bloque (Fase 2); sin callback en tiempo real. La historia ya está en _conversation_history (LLMProcessor la actualiza).

### Decisión 6.4 — Ruta simulador V2

- **Decisión**: En `routes_simulator_v2` se instancia `V2CallPersistenceAdapter(AsyncSessionLocal)` y se pasa al orquestador como `persistence_port`, y `stream_id=client_id`.
- **Motivo**: Cada sesión WebSocket tiene un client_id único; queda registrada en BD como una llamada con sus transcripciones al cerrar.

### Nota 6.5 — “Desde cero” y uso de la BD existente

- **Duda registrada**: El plan establece construir todo desde cero; podría interpretarse como “BD también desde cero, sin intervenir con legacy”.
- **Decisión tomada (Fase 2)**: Lo construido desde cero es el **código** (port, adapter, flujo en orquestador). El **almacenamiento** es la misma BD (tablas `calls`, `transcripts`) para un solo Historial operativo. No se modifica el esquema legacy; solo se escribe en él desde código V2.
- **Si más adelante se requiriera BD/schema V2 propio**: El port CallPersistencePort no cambia; se implementaría un adapter distinto (p. ej. tablas `calls_v2`/`transcripts_v2` o otra BD) y la UI V2 leería de ahí. Queda documentado en `docs/PLAN_TRABAJO_PRODUCCION.md` (§ Alcance de “construir desde cero”: código vs. almacenamiento).

---

## Archivos creados/modificados en Paso 6

| Ruta | Propósito |
|------|-----------|
| `docs/REVISION_LEGACY_FASE_2.md` | Revisión legacy: call/transcript repos, db_service, orquestador; conclusiones y contrato V2. |
| `app_v2/domain/ports/call_persistence_port.py` | CallPersistencePort (ABC): create_call, save_transcripts, end_call. |
| `app_v2/domain/ports/__init__.py` | Export CallPersistencePort. |
| `app_v2/application/orchestrator.py` | Parámetros opcionales stream_id, persistence_port; create_call en start(); save_transcripts + end_call en stop(). |
| `app/adapters/outbound/persistence/v2_call_persistence_adapter.py` | V2CallPersistenceAdapter(session_factory) implementa CallPersistencePort vía db_service. |
| `app/api/routes_simulator_v2.py` | Persistence adapter, stream_id=client_id, persistence_port en Orchestrator. |

---

## Paso 7 — UI V2 (Fase 3 del plan de producción)

**Revisión legacy**: `docs/REVISION_LEGACY_FASE_3.md`. Referencia: templates/dashboard.html, partials (panel_simulator, tab_*), static/js (main.js, dashboard/store.v2.js, simulator.v2.js), routers dashboard/config/history.

### Decisión 7.1 — Ruta y template V2

- **Decisión**: Nueva ruta GET `/dashboard/v2` que renderiza `dashboard_v2.html` con el **mismo contexto** que GET /dashboard (config_json, voices_json, styles_json, models_json, langs_json, history). Helper `_dashboard_context(request, db)` en `dashboard.py` construye el contexto; ambas rutas lo reutilizan.
- **Motivo**: Config e historial siguen leyendo la misma BD que el backend V2; una sola fuente de verdad. UI V2 convive con la actual (dos entradas).

### Decisión 7.2 — Simulador conectado a V2

- **Decisión**: En `app/static/js/dashboard/simulator.v2.js`, en `startTest()`, si `window.USE_V2_SIMULATOR === true` se usa `wsUrl = \`${protocol}//${host}/ws/simulator/v2/stream\``; en caso contrario la URL legacy `/api/v1/ws/media-stream?client=browser`. En `dashboard_v2.html` se inyecta `<script>window.USE_V2_SIMULATOR = true;</script>` antes de cargar main.js.
- **Motivo**: Un solo código de simulador (SimulatorMixin); solo cambia la URL según la página. Formato de mensajes (event 'start', 'media' con media.payload) ya compatible con el backend V2.

### Decisión 7.3 — Copia del template

- **Decisión**: `dashboard_v2.html` es copia de `dashboard.html` con: título "Panel V2 - Asistente IA"; logo en sidebar con badge "V2" (estilo emerald/teal); script que define `window.USE_V2_SIMULATOR = true` antes de main.js. Resto de partials e inyección de datos igual.
- **Motivo**: Editar solo lo necesario; mismo store y misma lógica de pestañas/config/historial.

### Decisión 7.4 — Config e historial

- **Decisión**: No se crean rutas API nuevas para UI V2. La misma config (inyectada en el template) y el mismo historial (history desde get_recent_calls) alimentan la vista; las APIs existentes (/api/config/update-json, /api/history/rows, etc.) siguen siendo las mismas y leen la BD que ya usa el backend V2.
- **Motivo**: Criterio de cierre "config e historial muestran datos coherentes con el backend V2" se cumple por compartir BD y contexto.

---

## Archivos creados/modificados en Paso 7

| Ruta | Propósito |
|------|-----------|
| `docs/REVISION_LEGACY_FASE_3.md` | Revisión legacy UI: templates, static, rutas; hallazgos y estrategia. |
| `app/templates/dashboard_v2.html` | Copia de dashboard.html con título V2, badge logo, window.USE_V2_SIMULATOR = true. |
| `app/static/js/dashboard/simulator.v2.js` | Elección de wsUrl según window.USE_V2_SIMULATOR; compatibilidad msg.data / msg.media.payload. |
| `app/routers/dashboard.py` | Helper _dashboard_context(); GET /dashboard y GET /dashboard/v2 que lo usan; dashboard_v2 renderiza dashboard_v2.html. |

---

## Paso 8 — Telefonía al core V2 (Fase 4 del plan de producción)

**Revisión legacy**: `docs/REVISION_LEGACY_FASE_4.md`. Referencia: `app/api/routes_telephony.py`, `app/adapters/telephony/transport.py` (TelephonyTransport), webhooks Twilio/Telnyx, formato audio mulaw 8kHz.

### Decisión 8.1 — Transport V2 para telephony

- **Decisión**: Nuevo adapter en `app/adapters/telephony/v2_telephony_transport.py`: **V2TelephonyTransport(websocket, protocol)** implementa `app_v2.domain.ports.AudioTransport`. send_audio: base64 del payload; mensaje con `event: "media"`, `streamSid` (Twilio) o `stream_id` + `track: "inbound_track"` (Telnyx). send_json y close (cierra WebSocket). set_stream_id para fijar stream_sid tras evento "start".
- **Motivo**: Misma URL `/api/v1/ws/media-stream` y mismo formato de mensajes que legacy; el handler pasa a usar Orchestrator V2 con este transport.

### Decisión 8.2 — Handler WebSocket con orquestador V2

- **Decisión**: En `app/api/routes_telephony.py` el WebSocket usa Orchestrator V2: ConfigAdapter(load_config_for_call), GroqWhisperSTTAdapter, GroqLLMAdapter, AzureTTSAdapter(output_format="mulaw_8k"), V2TelephonyTransport, V2CallPersistenceAdapter(AsyncSessionLocal). stream_id=client_id (call_control_id o UUID), client_type=client (twilio|telnyx), persistence_port inyectado. Comprobación is_calls_allowed() antes de aceptar; CriticalCallError en start() y en process_audio() → report_critical_error, disconnect y cierre.
- **Motivo**: Paridad con simulador V2: mismo core, políticas de error y persistencia; solo cambia el transport y el formato TTS (mulaw_8k para telephony).

### Decisión 8.3 — Eventos y URL

- **Decisión**: URL del WebSocket se mantiene: `/api/v1/ws/media-stream`. TwiML y Telnyx siguen apuntando a la misma URL. En el handler: evento "start" → stream_sid desde start.streamSid o msg.stream_id; transport.set_stream_id(stream_sid). Evento "media" → decodificar media.payload (base64) a bytes y orchestrator.process_audio(audio_bytes). Eventos "connected", "stop", "client_interruption" tratados sin cambio de flujo.
- **Motivo**: Sin cambios en integraciones externas; solo el código del handler migra a V2.

### Decisión 8.4 — Eliminación de dependencias legacy en el handler

- **Decisión**: Se dejan de usar en este endpoint VoiceOrchestratorV2, get_voice_ports y TelephonyTransport; se eliminan sus imports. Las rutas HTTP (incoming-call, call_control, helpers answer/streaming/noise) no se modifican.
- **Motivo**: Solo el flujo de media del WebSocket pasa a V2; webhooks y respuestas TwiML/Telnyx siguen igual.

---

## Archivos creados/modificados en Paso 8

| Ruta | Propósito |
|------|-----------|
| `app/adapters/telephony/v2_telephony_transport.py` | V2TelephonyTransport(websocket, protocol) implementa AudioTransport; send_audio (media base64), send_json, set_stream_id, close. |
| `app/api/routes_telephony.py` | Imports V2 (Orchestrator, adapters, CriticalCallError, persistence, policy). WebSocket: is_calls_allowed; V2TelephonyTransport; Orchestrator con TTS mulaw_8k, persistence, stream_id; manejo CriticalCallError; eventos start/media/stop. |

---

## Paso 9 — Paridad: extracción post-llamada (Fase 5 del plan de producción)

**Revisión legacy**: `docs/REVISION_LEGACY_FASE_5.md`. Referencia: orchestrator_v2.stop() (extracción, update_call_extraction, end_call), extraction_service, db_service.update_call_extraction, Call.extracted_data.

### Decisión 9.1 — ExtractionPort en app_v2

- **Decisión**: Nuevo port `ExtractionPort` en `app_v2/domain/ports/extraction_port.py`: `extract(stream_id, items: list[tuple[str, str]]) -> dict`. Retorna diccionario estructurado (summary, intent, sentiment, extracted_entities, next_action) o {} si falla. El adapter en app usa extraction_service (Groq LLM); app_v2 no importa app.
- **Motivo**: Paridad con legacy: al cierre de llamada se extrae información del diálogo y se guarda en Call.extracted_data para Historial e integraciones.

### Decisión 9.2 — update_call_extraction en CallPersistencePort

- **Decisión**: Añadido método `update_call_extraction(call_id, extracted_data: dict)` a CallPersistencePort. V2CallPersistenceAdapter lo implementa con db_service.update_call_extraction(session, call_id, extracted_data).
- **Motivo**: Misma BD y mismo campo Call.extracted_data que el legacy.

### Decisión 9.3 — Orquestador con extraction_port opcional

- **Decisión**: Orchestrator acepta parámetro opcional `extraction_port: ExtractionPort | None`. En stop(): tras save_transcripts, si hay extraction_port, stream_id e items, se llama extraction_port.extract(stream_id, items); si el resultado no es vacío, persistence_port.update_call_extraction(call_id, extracted); luego end_call. Si la extracción falla o devuelve {}, se continúa con end_call sin bloquear.
- **Motivo**: Flujo único en el orquestador; las rutas inyectan el adapter de extracción (V2ExtractionAdapter) en simulador y telephony.

### Decisión 9.4 — V2ExtractionAdapter en app

- **Decisión**: `app/adapters/outbound/extraction/v2_extraction_adapter.py`: V2ExtractionAdapter implementa ExtractionPort; convierte items (role, content) a lista de dicts y llama extraction_service.extract_post_call(stream_id, history). Excepciones → retorno {}.
- **Motivo**: Reutilizar el servicio legacy sin acoplar app_v2 a app.

### Decisión 9.5 — Fuera de alcance Fase 5

- **Decisión**: CRM manager (update_status al cierre) y uso de client_state dentro del orquestador no implementados; quedan registrados en REVISION_LEGACY_FASE_5.md como posible extensión. Schema de extracción configurable por perfil: paridad con schema fijo (el de extraction_service).
- **Motivo**: Prioridad en extracción y update_call_extraction para paridad de Historial.

### Nota 9.6 — Configuración desde env (sin hardcodear)

- **Decisión**: Modelo de extracción configurable por env: añadido `GROQ_EXTRACTION_MODEL` en `app/core/config.py` (default `llama-3.1-8b-instant`). `extraction_service` usa `settings.GROQ_EXTRACTION_MODEL`. Alineado con convención: Docker/Coolify, variables no compartidas; todo lo configurable desde env.

---

## Archivos creados/modificados en Paso 9

| Ruta | Propósito |
|------|-----------|
| `docs/REVISION_LEGACY_FASE_5.md` | Revisión legacy: cierre, extracción, update_call_extraction; brecha y decisiones. |
| `app_v2/domain/ports/extraction_port.py` | ExtractionPort (ABC): extract(stream_id, items) -> dict. |
| `app_v2/domain/ports/call_persistence_port.py` | Añadido update_call_extraction(call_id, extracted_data). |
| `app_v2/domain/ports/__init__.py` | Export ExtractionPort. |
| `app/adapters/outbound/extraction/__init__.py` | Paquete; export V2ExtractionAdapter. |
| `app/adapters/outbound/extraction/v2_extraction_adapter.py` | V2ExtractionAdapter: extraction_service.extract_post_call. |
| `app/adapters/outbound/persistence/v2_call_persistence_adapter.py` | update_call_extraction → db_service.update_call_extraction. |
| `app_v2/application/orchestrator.py` | Parámetro extraction_port; en stop(): extract → update_call_extraction → end_call. |
| `app/api/routes_simulator_v2.py` | Inyección V2ExtractionAdapter como extraction_port. |
| `app/api/routes_telephony.py` | Inyección V2ExtractionAdapter como extraction_port. |
| `app/core/config.py` | GROQ_EXTRACTION_MODEL (env; default llama-3.1-8b-instant). |
| `app/services/extraction_service.py` | Modelo desde settings.GROQ_EXTRACTION_MODEL (sin hardcodear). |

---

## Paso 10 — Preparación para producción (Fase 6 del plan)

**Revisión legacy**: `docs/REVISION_LEGACY_FASE_6.md`. Referencia: config.py, main.py (lifespan), system.py (health), global_call_policy (env), COOLIFY_DEPLOY, .env.example.

### Decisión 10.1 — Liveness probe

- **Decisión**: Añadido GET `/health` en `app/main.py` que responde 200 `{"status": "ok"}` sin depender de BD ni Redis. GET `/api/system/health` se mantiene como readiness (comprueba BD y Redis).
- **Motivo**: Coolify u orquestadores pueden usar `/health` como liveness y `/api/system/health` como readiness; no hardcodear rutas en documentación sin ofrecer la ruta esperada.

### Decisión 10.2 — Documentación de variables de entorno

- **Decisión**: Creado `docs/VARIABLES_ENTORNO.md` con lista completa: obligatorias (POSTGRES_USER, POSTGRES_PASSWORD, ADMIN_API_KEY), BD opcionales, AI (GROQ_*, AZURE_*), telephony (Twilio/Telnyx), política global (GLOBAL_STOP_*, ADMIN_NOTIFICATION_WEBHOOK_URL), infra (REDIS_URL, APP_ENV, etc.). Incluye health y reanudación de paro global.
- **Motivo**: Una sola referencia para Coolify y despliegues; sin hardcodear valores; alineado con convención de env.

### Decisión 10.3 — Documentación operativa

- **Decisión**: Creado `docs/OPERACION.md`: health (liveness vs readiness), reanudar paro global (POST /admin/reset-global-stop), logs (eventos critical_call_error, global_call_stop_activated), enlace a VARIABLES_ENTORNO.
- **Motivo**: Criterio de cierre Fase 6: documentación que permita operar y reaccionar ante errores.

### Decisión 10.4 — Actualización de guías existentes

- **Decisión**: COOLIFY_DEPLOY.md: enlace a VARIABLES_ENTORNO.md y OPERACION.md; variables de política V2 y GROQ_EXTRACTION_MODEL. DEPLOY_CHECKLIST.md: rutas correctas (/health, /api/system/health) y enlaces a docs. .env.example: bloque GLOBAL_STOP_*, ADMIN_NOTIFICATION_WEBHOOK_URL, GROQ_EXTRACTION_MODEL.
- **Motivo**: Consistencia entre documentación y código; Coolify sin compartir env.

---

## Archivos creados/modificados en Paso 10

| Ruta | Propósito |
|------|-----------|
| `docs/REVISION_LEGACY_FASE_6.md` | Revisión legacy: config, health, main, env; hallazgos y decisiones. |
| `docs/VARIABLES_ENTORNO.md` | Referencia completa de variables de entorno; health y reanudación. |
| `docs/OPERACION.md` | Operación: health, paro global, logs. |
| `app/main.py` | GET /health (liveness). |
| `COOLIFY_DEPLOY.md` | Enlaces a VARIABLES_ENTORNO y OPERACION; vars política V2 y extracción. |
| `DEPLOY_CHECKLIST.md` | Rutas /health y /api/system/health; enlaces a docs. |
| `.env.example` | Bloque GLOBAL_STOP_*, ADMIN_NOTIFICATION_WEBHOOK_URL, GROQ_EXTRACTION_MODEL. |

### Nota — Transcripción en vivo en panel simulador (log en tiempo real)

- **Decisión**: El panel del simulador muestra transcripción en tiempo real (user/assistant) como información temporal, tipo log; no sustituye ni modifica el historial (que se persiste al cierre). El backend V2 emite mensajes `{ type: "transcript", role, text }` por el WebSocket cuando el cliente es `browser`.
- **Implementación**: Pipeline acepta callback opcional `on_frame(frame)`; tras cada paso se invoca con el frame resultante. El orquestador define `_emit_transcript_live`: si `client_type == "browser"` y el frame es TextFrame, envía ese JSON por el transport. El frontend (simulator.v2.js) ya manejaba `msg.type === 'transcript'` y lo añade a `this.transcripts` con scroll.
- **Archivos**: `app_v2/application/pipeline.py` (parámetro `on_frame`); `app_v2/application/orchestrator.py` (`_emit_transcript_live`, llamada a `pipeline.run(..., on_frame=...)`).

---

## Próximos pasos (no ejecutados aún)

- Ninguno pendiente en el plan actual (Fases 1–6 completadas).

---

*Actualizado: 2026-02-09 — Paso 10 (Fase 6 preparación para producción) completado y documentado.*

*Este documento se actualiza en cada paso. No eliminar entradas pasadas; solo añadir.*
