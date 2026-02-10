# Auditoría del Core – Arquitectura Hexagonal

**Fecha**: 2026-02-09  
**Alcance**: Core del proyecto (Dominio + Capa de Aplicación / Orquestación)  
**Objetivo**: Identificar archivos a revisar, organización y funcionamiento para actualizar la documentación.

---

## 1. Resumen ejecutivo

En un **modelo hexagonal**, el **core** es el centro de la aplicación: **no depende de frameworks ni de infraestructura concreta**. En este proyecto el core se reparte en:

| Capa hexagonal | Ubicación en el proyecto | Rol |
|-----------------|--------------------------|-----|
| **Dominio** | `app/domain/` | Entidades, value objects, puertos (interfaces), reglas de negocio, FSM |
| **Casos de uso (dominio)** | `app/domain/use_cases/` | Lógica de negocio pura (turn end, barge-in, execute tool) |
| **Casos de uso (voz)** | `app/use_cases/` | Orquestación de STT/LLM/TTS (transcribe, synthesize, generate response) |
| **Aplicación / Orquestación** | Parte de `app/core/` | Pipeline, frames, orquestador, factory de pipeline, control channel |

La carpeta `app/core/` mezcla **núcleo de aplicación** (orchestrator, pipeline, frames, processor) con **infraestructura compartida** (config, auth, redis, logging). Para la auditoría del “core hexagonal” se consideran solo los archivos que implementan dominio y orquestación.

---

## 2. Archivos a revisar por capa

### 2.1 Dominio puro (`app/domain/`)

Archivos que **no deben** depender de `app/core` (salvo tipos mínimos), adapters ni bases de datos.

| Archivo | Propósito | Dependencias actuales |
|---------|-----------|------------------------|
| **Ports (interfaces)** | | |
| `domain/ports/__init__.py` | Export de puertos | Solo domain |
| `domain/ports/audio_transport.py` | Interface AudioTransport | - |
| `domain/ports/cache_port.py` | Interface CachePort | - |
| `domain/ports/call_repository_port.py` | CallRecord, CallRepositoryPort | - |
| `domain/ports/config_repository_port.py` | ConfigDTO, ConfigRepositoryPort, ConfigNotFoundException | - |
| `domain/ports/llm_port.py` | LLMPort, LLMRequest, LLMMessage, LLMException | - |
| `domain/ports/stt_port.py` | STTPort, STTConfig, STTEvent, STTRecognizer, STTResultReason, STTException | - |
| `domain/ports/tts_port.py` | TTSPort, TTSRequest, TTSException, VoiceMetadata | - |
| `domain/ports/transcript_repository_port.py` | TranscriptRepositoryPort | - |
| `domain/ports/tool_port.py` | ToolPort (usa domain/models) | domain.models.tool_models |
| `domain/ports/provider_config.py` | STTProviderConfig, LLMProviderConfig, TTSProviderConfig | - |
| **Models** | | |
| `domain/models/__init__.py` | Package | - |
| `domain/models/llm_models.py` | LLMChunk, LLMFunctionCall, etc. | - |
| `domain/models/tool_models.py` | ToolDefinition, ToolRequest, ToolResponse | - |
| **State (FSM)** | | |
| `domain/state/__init__.py` | Export state | - |
| `domain/state/conversation_state.py` | ConversationState, ConversationFSM, StateTransitionEvent | - |
| **Value objects** | | |
| `domain/value_objects/__init__.py` | Export value objects | - |
| `domain/value_objects/call_context.py` | CallMetadata, ContactInfo | - |
| `domain/value_objects/voice_config.py` | VoiceConfig, VoiceStyle, AudioFormat, AudioMode | - |
| **Lógica de configuración** | | |
| `domain/config_logic.py` | apply_client_overlay (browser/twilio/telnyx) | - |
| **Casos de uso de dominio** | | |
| `domain/use_cases/__init__.py` | Export use cases | - |
| `domain/use_cases/detect_turn_end.py` | DetectTurnEndUseCase (VAD timer) | - |
| `domain/use_cases/execute_tool.py` | ExecuteToolUseCase (ToolPort) | domain.models, domain.ports.tool_port |
| `domain/use_cases/handle_barge_in.py` | HandleBargeInUseCase, BargeInCommand | - |
| **Excepciones** | | |
| `domain/exceptions/__init__.py` | Package | - |
| `domain/exceptions/tool_exceptions.py` | Excepciones de herramientas | - |

**Total dominio**: 26 archivos (incl. `__init__.py`).

---

### 2.2 Casos de uso de voz (`app/use_cases/`)

Orquestan flujos de voz (STT → LLM → TTS) usando puertos y, en algún caso, utilidades de aplicación.

| Archivo | Propósito | Dependencias |
|---------|-----------|--------------|
| `use_cases/__init__.py` | Export GenerateResponse, SynthesizeText, TranscribeAudio | - |
| `use_cases/voice/__init__.py` | Package | - |
| `use_cases/voice/transcribe_audio.py` | TranscribeAudioUseCase | domain (puertos STT) |
| `use_cases/voice/synthesize_text.py` | SynthesizeTextUseCase | domain.value_objects.VoiceConfig |
| `use_cases/voice/generate_response.py` | GenerateResponseUseCase | app.core.prompt_builder |

**Nota**: `generate_response.py` depende de `app.core.prompt_builder`; para un core “puro” podría moverse la construcción de prompts a dominio o inyectarse como interfaz.

**Total use_cases**: 5 archivos.

---

### 2.3 Núcleo de aplicación en `app/core/`

Solo los que forman parte del **flujo hexagonal** (frames, pipeline, orquestador, control, factory, puertos de voz).

| Archivo | Propósito | ¿Core hexagonal? |
|---------|-----------|-------------------|
| **Frames y pipeline** | | |
| `core/frames.py` | Frame, SystemFrame, DataFrame, ControlFrame, AudioFrame, TextFrame, etc. | ✅ Sí |
| `core/processor.py` | FrameProcessor, FrameDirection | ✅ Sí |
| `core/pipeline.py` | Pipeline, PipelineSource, PipelineSink, cola con prioridad | ✅ Sí |
| `core/pipeline_factory.py` | PipelineFactory (construye cadena STT→VAD→Agg→LLM→TTS→Metrics→Reporter→Sink) | ✅ Sí |
| **Orquestación** | | |
| `core/orchestrator_v2.py` | VoiceOrchestratorV2 (transport, pipeline, FSM, managers) | ✅ Sí |
| `core/control_channel.py` | ControlChannel, ControlSignal (INTERRUPT, CANCEL, etc.) | ✅ Sí |
| **Puertos y registro** | | |
| `core/voice_ports.py` | VoicePorts, get_voice_ports(), registro de providers | ✅ Sí (factory de puertos) |
| `core/adapter_registry.py` | AdapterRegistry (hot-swap de adapters) | ✅ Sí |
| **Audio (aplicación)** | | |
| `core/audio/__init__.py` | Package | ✅ Sí |
| `core/audio/hold_audio.py` | HoldAudioPlayer (“thinking” durante tools) | ✅ Sí (usa AudioManager/transport) |
| `core/audio_config.py` | AudioConfig (for_browser, for_twilio, for_telnyx) | ✅ Sí |
| `core/audio_manager.py` | (Si existe y es lógica de aplicación) | Revisar |
| `core/managers/__init__.py` | AudioManager, CRMManager | ✅ Sí |
| `core/managers/audio_manager.py` | AudioManager (AudioTransport) | ✅ Sí |
| `core/managers/crm_manager.py` | CRMManager | ✅ Sí |
| **Prompt y helpers** | | |
| `core/prompt_builder.py` | Construcción de system prompt / contexto | ✅ Sí (usado por GenerateResponseUseCase y LLM) |
| `core/conversation_helpers.py` | Helpers de conversación | Revisar |
| **VAD (modelo)** | | |
| `core/vad/` (model.py, analyzer.py, data/) | Silero VAD (ONNX) | ✅ Sí (lógica de detección) |

**Resto de `app/core/`** (config, auth, redis, logging, seguridad, HTTP, etc.) se considera **infraestructura compartida**, no “core hexagonal”:

- `config.py`, `config_utils.py`, `exceptions.py`
- `auth_simple.py`, `csrf.py`, `security_middleware.py`, `webhook_security.py`
- `redis_state.py`, `state_manager.py`
- `logging_config.py`, `secure_logging.py`, `tracing.py`, `metrics.py`, `decorators.py`
- `http_client.py`, `input_sanitization.py`
- `dialer.py`, `event_handlers.py`
- `audio_processor.py`, `audio_streamer.py`, `audio_utils.py` (revisar si son solo I/O)

---

## 3. Cómo está organizado y cómo funciona

### 3.1 Flujo de dependencias (ideal)

```
Routers / API / WebSocket
         ↓
   VoiceOrchestratorV2  (core/orchestrator_v2.py)
         ↓
   Pipeline (core/pipeline.py) ← PipelineFactory (core/pipeline_factory.py)
         ↓
   Processors (app/processors/) → usan Puertos (domain/ports) y Use Cases (domain/use_cases)
         ↓
   Adapters (app/adapters/) implementan Puertos
```

- **Dominio**: solo tipos, interfaces y reglas; sin imports de `app.core` (salvo que se decida extraer `prompt_builder` a un puerto).
- **Orquestador**: depende de domain (ports, state, use_cases, value_objects, config_logic) y de core (frames, pipeline, pipeline_factory, control_channel, managers, voice_ports, audio, audio_config).
- **Pipeline y processors**: dependen de `core.frames`, `core.processor` y de domain (ports, use_cases, models).

### 3.2 Puntos clave del core

1. **Puertos** (`domain/ports`): STT, LLM, TTS, ConfigRepository, CallRepository, TranscriptRepository, ToolPort, AudioTransport, CachePort. Configuración de proveedores en `provider_config.py`.
2. **FSM** (`domain/state/conversation_state.py`): ConversationState (IDLE, LISTENING, PROCESSING, SPEAKING, INTERRUPTED, TOOL_EXECUTING, ENDING), ConversationFSM con transiciones deterministas.
3. **Frames** (`core/frames.py`): Base Frame (trace_id, span_id), SystemFrame (Start, End, Cancel, UserStarted/StoppedSpeaking, Backpressure, etc.), DataFrame (Audio, Text), ControlFrame. Prioridad para no bloquear señales de control.
4. **Pipeline** (`core/pipeline.py`): Cadena de FrameProcessor, cola con prioridad y tamaño máximo, backpressure.
5. **PipelineFactory** (`core/pipeline_factory.py`): Crea la secuencia STTProcessor → VADProcessor → ContextAggregator → LLMProcessor → TTSProcessor → MetricsProcessor → TranscriptReporter → PipelineOutputSink; inyecta DetectTurnEndUseCase, ExecuteToolUseCase, ControlChannel, puertos.
6. **VoiceOrchestratorV2**: Gestiona transporte, configuración (apply_client_overlay), FSM, pipeline (vía factory), managers (Audio, CRM), uso de SynthesizeTextUseCase y servicios externos (ej. extraction_service).
7. **VoicePorts** (`core/voice_ports.py`): Factory que obtiene STT/LLM/TTS/Config/Call/Transcript desde configuración y ProviderRegistry; usa `app.infrastructure.provider_registry` y adapters concretos (Azure, Google, Groq, etc.).

### 3.3 Dependencias del dominio (comprobadas)

- `domain/ports/tool_port.py` → `domain/models/tool_models.py` (correcto).
- `domain/use_cases/execute_tool.py` → `domain.models`, `domain.ports.tool_port` (correcto).
- El resto del dominio no importa `app.core` ni `app.adapters`.

### 3.4 Dependencias del core de aplicación

- **orchestrator_v2**: domain (config_logic, ports, state, use_cases, value_objects), core (control_channel, frames, managers, pipeline, pipeline_factory, audio_config), use_cases.voice (SynthesizeTextUseCase), services (extraction_service).
- **pipeline_factory**: core (audio.hold_audio, control_channel, managers, pipeline), domain (ports LLM/STT/TTS, use_cases DetectTurnEnd, ExecuteTool), processors (logic y output).
- **voice_ports**: core (adapter_registry, config), domain (ports, provider_config), adapters e infrastructure (provider_registry, DB).

---

## 4. Listado único: archivos a revisar en la auditoría del core

Orden sugerido para revisión y documentación.

### 4.1 Dominio (primero)

1. `app/domain/ports/__init__.py`
2. `app/domain/ports/audio_transport.py`
3. `app/domain/ports/cache_port.py`
4. `app/domain/ports/call_repository_port.py`
5. `app/domain/ports/config_repository_port.py`
6. `app/domain/ports/llm_port.py`
7. `app/domain/ports/stt_port.py`
8. `app/domain/ports/tts_port.py`
9. `app/domain/ports/transcript_repository_port.py`
10. `app/domain/ports/tool_port.py`
11. `app/domain/ports/provider_config.py`
12. `app/domain/models/llm_models.py`
13. `app/domain/models/tool_models.py`
14. `app/domain/state/conversation_state.py`
15. `app/domain/value_objects/call_context.py`
16. `app/domain/value_objects/voice_config.py`
17. `app/domain/config_logic.py`
18. `app/domain/use_cases/detect_turn_end.py`
19. `app/domain/use_cases/execute_tool.py`
20. `app/domain/use_cases/handle_barge_in.py`
21. `app/domain/exceptions/tool_exceptions.py` (si existe)

### 4.2 Casos de uso de voz

22. `app/use_cases/voice/transcribe_audio.py`
23. `app/use_cases/voice/synthesize_text.py`
24. `app/use_cases/voice/generate_response.py`

### 4.3 Núcleo de aplicación (core)

25. `app/core/frames.py`
26. `app/core/processor.py`
27. `app/core/pipeline.py`
28. `app/core/pipeline_factory.py`
29. `app/core/control_channel.py`
30. `app/core/orchestrator_v2.py`
31. `app/core/voice_ports.py`
32. `app/core/adapter_registry.py`
33. `app/core/audio_config.py`
34. `app/core/audio/hold_audio.py`
35. `app/core/managers/audio_manager.py`
36. `app/core/managers/crm_manager.py`
37. `app/core/prompt_builder.py`
38. `app/core/vad/model.py`
39. `app/core/vad/analyzer.py`
40. `app/core/conversation_helpers.py` (revisar si es solo aplicación)

**Total recomendado para esta auditoría**: 40 archivos (sin contar `__init__.py` ni documentación).

---

## 5. Recomendaciones para la documentación

1. **Actualizar ARCHITECTURE.md**  
   - Dejar explícito qué es “core” en sentido hexagonal: `domain/` + `use_cases/` + los archivos listados en §2.3 de este informe.  
   - Añadir un diagrama de capas donde dominio no dependa de core ni de adapters.

2. **Añadir docs/CORE_HEXAGONAL.md** (o sección en ARCHITECTURE.md)  
   - Lista de puertos y responsabilidades.  
   - Descripción de la FSM (estados y transiciones).  
   - Tipos de frames y prioridades.  
   - Flujo: WebSocket/API → Orchestrator → Pipeline → Processors → Ports → Adapters.

3. **Documentar dependencias**  
   - Tabla o grafo: “domain no importa core/adapters”; “orchestrator importa domain + core + use_cases”; “voice_ports importa domain + core + adapters + infrastructure”.

4. **Criterio de “core” en core/**  
   - En `app/core/`, documentar qué archivos son “application core” (frames, pipeline, orchestrator, voice_ports, etc.) y cuáles son “shared infrastructure” (config, auth, redis, logging, etc.) para no mezclar conceptos en la documentación.

5. **GenerateResponseUseCase y prompt_builder**  
   - Decidir si la construcción de prompts debe ser un puerto (interface en domain) implementado en core o en un adapter, para mantener el dominio libre de detalles de aplicación.

---

## 6. Próximos pasos sugeridos

1. Revisar en detalle cada archivo de la lista §4 (orden: dominio → use_cases → core).  
2. Comprobar que ningún archivo de `domain/` importe `app.core` o `app.adapters`.  
3. Actualizar ARCHITECTURE.md con la definición de core y el diagrama de capas.  
4. Crear o ampliar docs/CORE_HEXAGONAL.md con puertos, FSM, frames y flujo.  
5. Opcional: extraer `prompt_builder` a un puerto si se quiere dominio 100% aislado.

---

*Documento generado en el marco de la auditoría del proyecto para actualizar la documentación según el modelo hexagonal.*
