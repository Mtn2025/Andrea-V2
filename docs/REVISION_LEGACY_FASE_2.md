# Revisión legacy — Fase 2: Persistencia al cierre de llamada (Historial)

**Objetivo de la revisión**: Identificar en legacy cómo se crea la llamada, se persisten las transcripciones y se cierra el registro en BD, para diseñar en V2 un contrato de cierre y un adapter que escriba en la misma BD sin acoplar app_v2 a app.

**Fecha de la revisión**: 2026-02-09  
**Fase del plan**: Fase 2 — Persistencia al cierre de llamada (Historial) en V2.

---

## 1. Ámbito revisado

| Ruta | Rol |
|------|-----|
| `app/domain/ports/call_repository_port.py` | CallRecord (DTO), CallRepositoryPort: create_call(stream_id, client_type, metadata) → CallRecord; end_call(call_id); get_call; update_call_extraction(call_id, extracted_data). |
| `app/domain/ports/transcript_repository_port.py` | TranscriptRepositoryPort: save(call_id, role, content). |
| `app/adapters/outbound/persistence/sqlalchemy_call_repository.py` | Implementación: session_factory; create_call usa db_service.create_call(session, session_id=stream_id, client_type); end_call y update_call_extraction delegan en db_service. |
| `app/adapters/outbound/persistence/sqlalchemy_transcript_repository.py` | Cola asíncrona; save() encola (call_id, role, content); worker llama db_service.log_transcript(session, session_id, role, content, call_db_id=call_id). |
| `app/services/db_service.py` | create_call(session, session_id, client_type) → call.id (evita duplicado por session_id); log_transcript(session, session_id, role, content, call_db_id); end_call(session, call_id) (end_time, status=completed); update_call_extraction(session, call_id, extracted_data). |
| `app/db/models.py` | Call: id, session_id, start_time, end_time, status, client_type, extracted_data. Transcript: id, call_id, role, content, timestamp. |
| `app/core/orchestrator_v2.py` | create_call en start() (stream_id, client_type, metadata) → call_db_id; transcript_repo.save(call_db_id, role, text) vía _handle_transcript (callback del pipeline); en stop(): extraction opcional, end_call(call_db_id). |

---

## 2. Hallazgos

### 2.1 Creación de llamada

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/core/orchestrator_v2.py` L197-202 | create_call(stream_id, client_type, metadata) justo después de crear call record; stream_id viene de initial_context_data (call_sid, stream_id, call_control_id) o uuid. | V2 puede recibir stream_id desde la ruta (client_id o uuid) y crear la llamada al inicio de la sesión para tener call_id. |
| `app/services/db_service.py` L14-28 | create_call: si ya existe Call con session_id, devuelve ese id; si no, crea Call(session_id=session_id, client_type=client_type), commit, return call.id. | Mismo contrato: session_id único, client_type; retorno es id. |

### 2.2 Persistencia de transcripciones

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/core/orchestrator_v2.py` L576-586 | _handle_transcript(role, text): transcript_repo.save(call_db_id, role, text); conversation_history.append({role, content}). Llamado desde el pipeline vía transcript_callback. | En V2 el orquestador ya mantiene _conversation_history (LLMMessage). Para Fase 2 podemos persistir todo al cierre: recorrer _conversation_history y guardar cada (role, content) con el mismo call_id. No es obligatorio replicar el callback en tiempo real. |
| `app/services/db_service.py` L30-51 | log_transcript(session, session_id, role, content, call_db_id=None): si no call_db_id, busca Call por session_id; crea Transcript(call_id, role, content), add, commit. | El adapter V2 puede llamar log_transcript en bucle con call_db_id conocido. |

### 2.3 Cierre de llamada y extracción

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/core/orchestrator_v2.py` L287-301 | En stop(): si call_db_id, (opcional) extraction_service.extract_post_call(stream_id, conversation_history) → update_call_extraction; luego end_call(call_db_id). | V2: end_call obligatorio al cierre; extracción post-llamada puede ser Fase 4 (paridad). Para Fase 2 solo: create_call al inicio, save_transcripts al cierre, end_call. |

### 2.4 Modelo Call y Transcript

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/db/models.py` L15-38 | Call: session_id (unique), start_time, end_time, status, client_type, extracted_data. Transcript: call_id FK, role, content, timestamp. | El adapter en app escribe en estas tablas; no hay que cambiar esquema. |

---

## 3. Conclusiones

### 3.1 Qué se toma como referencia

- **Flujo**: Crear llamada al inicio (stream_id, client_type) → obtener call_id; al cierre guardar transcripciones (lista role/content) y end_call(call_id).
- **BD**: Misma tabla `calls` y `transcripts`; db_service.create_call, log_transcript, end_call. Opcional update_call_extraction en fases posteriores.
- **stream_id**: Identificador único de sesión (en simulador puede ser client_id de la ruta).

### 3.2 Contrato V2 propuesto

- **Port en app_v2**: `CallPersistencePort` (opcional para el orquestador).
  - `create_call(stream_id: str, client_type: str) -> int | None`: crea registro y devuelve call_id.
  - `save_transcripts(call_id: int, items: list[tuple[str, str]])`: items = [(role, content), ...]; persiste en orden.
  - `end_call(call_id: int) -> None`: marca llamada como completada.
- **Orquestador V2**: Recibe el port de forma opcional. En start(): si port, create_call(stream_id, client_type) y guarda call_id. En stop(): si port y call_id, convierte _conversation_history a lista (role, content), save_transcripts, end_call. Necesita stream_id inyectado (ruta lo pasa).
- **Adapter en app**: Implementa el port usando AsyncSessionLocal, db_service.create_call, en bucle db_service.log_transcript, db_service.end_call. Sin cola asíncrona en Fase 2 (guardado síncrono al cierre).

### 3.3 Qué no se replica en Fase 2

- Cola asíncrona de transcripciones (SQLAlchemyTranscriptRepository._queue): en V2 guardamos todo en bloque al cierre.
- Extracción post-llamada: fuera de alcance de Fase 2; se puede añadir en paridad (Fase 4/5).
- metadata en create_call: el legacy pasa initial_context_data; db_service.create_call no lo persiste en el modelo Call actual. El adapter V2 puede pasar metadata vacío o ignorarlo.

### 3.4 Dudas resueltas

- **¿Crear llamada al inicio o al final?** Al inicio, para tener call_id y poder asociar transcripciones; igual que legacy.
- **¿Transcripciones en tiempo real o al cierre?** Al cierre en Fase 2 (más simple); el orquestador ya tiene _conversation_history (system no se persiste como transcript; solo user y assistant).

---

## 4. Referencias cruzadas

- Plan: `docs/PLAN_TRABAJO_PRODUCCION.md` — Fase 2.
- Build Log: `docs/APP_V2_BUILD_LOG.md` — Paso 6 (por crear).
- Convenciones: `docs/CONVENCIONES_DOCUMENTACION.md`.

---

*Revisión legacy cerrada. Próximo paso: definir CallPersistencePort en app_v2, adapter en app, integrar en orquestador y ruta simulador V2; registrar en Build Log.*
