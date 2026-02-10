# Revisión del core – Hallazgos (centro y vinculaciones)

**Fecha**: 2026-02-09  
**Alcance**: Centro del core hexagonal y sus vinculaciones (front, back, BD).  
**Objetivo**: Confirmar que los archivos cumplen su función, detectar código obsoleto, redundante, incompleto o con errores.

---

## Resumen ejecutivo

| Categoría | Cantidad | Acción |
|-----------|----------|--------|
| **Errores / bugs** | 2 | Corregir |
| **Inconsistencias / contrato** | 2 | Documentar / alinear port |
| **Código redundante / no usado** | 2 | Opcional: limpiar o documentar |
| **Mejoras menores (tipos, estilo)** | 3 | Opcional |
| **OK / sin cambios** | Resto | - |

---

## 1. Dominio (`app/domain/`)

### 1.1 Ports

- **audio_transport, cache_port, call_repository_port, transcript_repository_port, tool_port, provider_config**: Correctos, sin dependencias de infra, usados por adapters.
- **llm_port, stt_port, tts_port**: Correctos. Excepciones con `retryable`/`provider` bien definidas.
- **config_repository_port**: Contrato distinto al uso real (ver §3).

**Mejoras menores (opcionales)**  
- `LLMRequest` (`llm_port.py`): `metadata: dict = None` → usar `metadata: dict | None = None` (y en `__post_init__` ya se trata None).  
- `TTSRequest` (`tts_port.py`): `style: str = None` → `style: str | None = None`.

### 1.2 Models

- **llm_models.py**: `LLMChunk`, `LLMFunctionCall`, `ToolDefinitionForLLM` usados. En `from_openai_format`, líneas 64–66 hay indentación inconsistente (espacios de más en `parsed_args`); no afecta ejecución pero conviene unificar.  
- **tool_models.py**: Correcto, usado por ExecuteToolUseCase y adapters.

### 1.3 State

- **conversation_state.py**: FSM bien definida, transiciones documentadas, usada por el orquestador. Sin hallazgos.

### 1.4 Value objects

- **call_context.py**: `CallMetadata` usa `datetime.utcnow` (deprecado en 3.12+); se puede migrar a `datetime.now(timezone.utc)` en una mejora futura.  
- **voice_config.py**: `VoiceConfig.from_db_config` usa `voice_pitch`, `voice_volume`, `voice_style_degree`; existen en `app/db/models.py` (AgentConfig). OK.

### 1.5 config_logic.py

- `apply_client_overlay` usa `getattr`/`try AttributeError` de forma defensiva. Los campos `voice_pacing_ms`, `silence_timeout_ms`, `conversation_pacing_mode` existen en el modelo. OK.

### 1.6 Domain use cases

- **detect_turn_end.py**: Usado por VADProcessor y PipelineFactory. OK.  
- **execute_tool.py**: Usado por LLMProcessor y PipelineFactory. Solo depende de domain. OK.  
- **handle_barge_in.py**:  
  - `HandleBargeInUseCase` y `BargeInCommand` **sí se usan** en `orchestrator_v2.handle_interruption`.  
  - **Redundancia**: `AudioManagerProtocol` y `PipelineProtocol` no se usan (el orquestador no inyecta pipeline/audio_manager en el use case; solo usa el comando). Son documentación implícita; se pueden dejar o eliminar para reducir ruido.

### 1.7 Exceptions

- **tool_exceptions.py**: Definiciones claras. No se usan en `ExecuteToolUseCase` (este devuelve `ToolResponse(success=False)` en lugar de lanzar); los adapters sí pueden lanzarlas. OK como contrato de dominio.

---

## 2. Núcleo de aplicación (`app/core/`)

### 2.1 frames.py, processor.py, pipeline.py

- **frames.py**: Tipos de frame coherentes (System/Data/Control), prioridad en pipeline. `ImageFrame`, `RMSFrame` existen; uso limitado pero no obstaculizan. OK.  
- **processor.py**: Base abstracta correcta. OK.  
- **pipeline.py**: Cola con prioridad, backpressure, `queue_frame`. Los procesadores se limpian vía `clear_queue()` (hasattr), no existe `clear_output_queue` en Pipeline; el orquestador usa `_clear_pipeline_output()` que itera procesadores y `audio_manager.clear_queue()`. OK.

### 2.2 pipeline_factory.py

- Ensambla STT → VAD → Aggregator → LLM → TTS → Metrics → Reporter → OutputSink. Inyecta `DetectTurnEndUseCase`, `ExecuteToolUseCase`, `ControlChannel`. Coherente con el flujo. OK.

### 2.3 orchestrator_v2.py

- Depende de domain (ports, state, use_cases, value_objects, config_logic) y de core (pipeline, frames, managers, control_channel, etc.).  
- **Config**: Llama a `config_repo.get_agent_config(agent_id)`; ese método **no está en ConfigRepositoryPort** (ver §3).  
- HandleBargeInUseCase y BargeInCommand se usan correctamente en `handle_interruption`.  
- `_load_config` usa `get_profile(self.client_type)` sobre el objeto devuelto por `get_agent_config` (ORM), lo cual está atado al adapter, no al port.  
- Resto de flujo (start, pipeline, FSM, audio, parada) coherente.

### 2.4 voice_ports.py

- Factory que instancia STT/LLM/TTS con fallbacks, config_repo, call_repo, transcript_repo, tools. Registro de providers correcto.  
- **Nota**: `audio_mode` se usa para TTS (twilio/telnyx/browser); el parámetro está bien usado. OK.

### 2.5 control_channel.py, adapter_registry.py, managers, audio (hold_audio), audio_config

- Revisión rápida: usados por orquestador o pipeline, sin código muerto evidente.

---

## 3. Vinculaciones y contratos

### 3.1 Entradas (front → core)

- **WebSocket / telephony**: `app/api/routes_telephony.py` y `app/api/routes_simulator.py` llaman a `get_voice_ports(audio_mode=...)` y construyen `VoiceOrchestratorV2` con los ports. Correcto.  
- **REST**: Dashboard y config usan `db_service.get_agent_config` directamente para CRUD de configuración; no pasan por el orquestador. Coherente.

### 3.2 Salidas (core → adapters / BD)

- **Config**: El orquestador usa `config_repo.get_agent_config(agent_id)` y espera un objeto con `.get_profile()`, `.name`, `.id` (ORM AgentConfig).  
- **ConfigRepositoryPort** solo define `get_config(profile: str) -> ConfigDTO`.  
- **Consecuencia**: El orquestador depende de la API **extendida** del adapter (método fuera del port) y del tipo ORM. Para hexagonal estricto habría que:  
  - Añadir al port algo como `get_agent_config(agent_id: int)` que devuelva un tipo “rich config” (o un DTO con soporte de perfil), y que el adapter implemente; o  
  - Hacer que el orquestador use solo `get_config(profile)` y mueva la resolución de perfil/agent_id a otro lugar.  
- **Recomendación**: Documentar esta desviación y, en una siguiente iteración, alinear el port con el uso real (p.ej. añadir `get_agent_config` al port y que devuelva un tipo de dominio, no el ORM).

### 3.3 Repositorio de configuración y BD

- **SQLAlchemyConfigRepository**:
  - `get_agent_config(agent_id)`: Llama a `db_service.get_agent_config(session)` y **no usa `agent_id`**. Comportamiento actual: siempre “default”/primer agente. El parámetro está **sin uso** (código muerto / multi-agente no implementado).  
  - **Bug**: `delete_agent_config(agent_id)` hace `db_service.get_agent_config(session, agent_id)`, pero `DBService.get_agent_config` solo tiene firma `(self, session)`. Esto provocará **TypeError** si se llama a `delete_agent_config`.  
- **DBService.get_agent_config(session)**: Solo obtiene por nombre `"default"`; no hay overload con `agent_id`.  
- **Acción**: Corregir `delete_agent_config` para no llamar a `get_agent_config(session, agent_id)` (p.ej. obtener por id con `session.get(AgentConfig, agent_id)` o equivalente), y documentar o implementar el uso de `agent_id` en `get_agent_config` si se quiere multi-agente.

---

## 4. Errores e inconsistencias a corregir

### 4.1 Bug: `delete_agent_config` (SQLAlchemyConfigRepository)

- **Archivo**: `app/adapters/outbound/repositories/sqlalchemy_config_repository.py`.  
- **Problema**: `db_service.get_agent_config(session, agent_id)` no existe; la firma es `get_agent_config(session)`.  
- **Acción**: Obtener el agente por id dentro del adapter (p.ej. `session.get(AgentConfig, agent_id)` o `select(AgentConfig).where(AgentConfig.id == agent_id)`), y luego borrarlo; no pasar `agent_id` a `db_service.get_agent_config`.

### 4.2 Parámetro `agent_id` ignorado en `get_agent_config`

- **Archivo**: mismo adapter.  
- **Problema**: `get_agent_config(agent_id)` no usa `agent_id`; siempre devuelve el config “default”.  
- **Acción**: Documentar (“solo agente default”) o implementar búsqueda por id (en adapter o en db_service) si se requiere multi-agente.

### 4.3 Contrato ConfigRepositoryPort vs uso en orquestador

- **Problema**: El port no declara `get_agent_config`; el orquestador depende de él y del tipo ORM.  
- **Acción**: Documentar en este informe; en siguiente iteración, ampliar el port (p.ej. `get_agent_config(agent_id)`) y que el adapter implemente sin filtrar tipos de dominio por ORM en el core.

---

## 5. Código redundante o opcional

### 5.1 Protocolos en handle_barge_in.py

- `AudioManagerProtocol` y `PipelineProtocol` no se usan en el orquestador (solo se usa `BargeInCommand`).  
- **Acción**: Opcional. Dejarlos como documentación o eliminarlos para simplificar.

### 5.2 LLMRequest.metadata / TTSRequest.style

- Tipos actuales `dict = None` / `str = None`.  
- **Acción**: Opcional. Cambiar a `dict | None = None` y `str | None = None` para consistencia y estáticos.

---

## 6. Resumen de archivos revisados (centro y vinculaciones)

| Zona | Archivos | Estado |
|------|----------|--------|
| Domain ports | 11 archivos | OK; mejoras menores opcionales en tipos |
| Domain models | llm_models, tool_models | OK; indentación menor en llm_models |
| Domain state | conversation_state | OK |
| Domain value_objects | call_context, voice_config | OK |
| Domain config_logic, use_cases, exceptions | 4 archivos | OK; Protocols en handle_barge_in no usados |
| Core frames, processor, pipeline, pipeline_factory | 4 archivos | OK |
| Core orchestrator_v2, voice_ports | 2 archivos | OK; dependen de API extra del config repo |
| Config adapter / DB | sqlalchemy_config_repository, db_service | Bug en delete_agent_config; agent_id no usado en get_agent_config |
| Entradas | routes_telephony, routes_simulator | OK |

---

## 7. Próximos pasos recomendados

1. **Corregir** `delete_agent_config` en `SQLAlchemyConfigRepository` (obtener por id en el adapter, sin llamar a `get_agent_config(session, agent_id)`).  
2. **Documentar** en el código o en ARCHITECTURE.md que `get_agent_config(agent_id)` actualmente ignora `agent_id` (solo agente default).  
3. Opcional: alinear **ConfigRepositoryPort** con el uso real (añadir `get_agent_config(agent_id)` al port y tipo de retorno de dominio).  
4. Opcional: limpiar tipos en LLMRequest/TTSRequest y indentación en llm_models; eliminar o mantener los Protocols en handle_barge_in según preferencia del equipo.  
5. Seguir con la revisión de **archivos consecuentes** (processors, adapters concretos, routers) en la siguiente fase.

---

*Revisión centrada en el centro del core y sus vinculaciones front, back y BD. Siguiente fase: revisión detallada de processors y adapters.*
