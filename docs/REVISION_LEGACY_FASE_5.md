# Revisión legacy — Fase 5: Paridad y robustez (cierre de llamada)

**Fecha**: 2026-02-09  
**Objetivo**: Identificar qué hace el legacy al cierre de llamada y qué debe replicar V2 para paridad (Historial e integraciones).

---

## 1. Código revisado

| Archivo | Relevancia |
|---------|------------|
| `app/core/orchestrator_v2.py` | stop(): pipeline, audio_manager, control_task; CRM; **extracción post-llamada**; end_call. |
| `app/services/extraction_service.py` | extract_post_call(session_id, history) → dict (summary, intent, sentiment, extracted_entities, next_action). |
| `app/services/db_service.py` | update_call_extraction(session, call_id, extracted_data); end_call(session, call_id). |
| `app/domain/ports/call_repository_port.py` | update_call_extraction(call_id, extracted_data). |
| `app/adapters/outbound/persistence/sqlalchemy_call_repository.py` | update_call_extraction → db_service.update_call_extraction. |
| `app/db/models.py` | Call.extracted_data (JSON). |
| `app/api/routes_telephony.py` | client_state en Telnyx (answer, streaming_start); no usado por orquestador en stop. |

---

## 2. Flujo de cierre en legacy (orchestrator_v2.stop())

1. Cancelar control_task y parar pipeline y audio_manager.
2. **CRM**: si hay crm_manager, `update_status(phone, "Call Ended")` (phone desde initial_context_data).
3. Si hay call_db_id:
   - **Extracción**: si hay conversation_history, `extraction_service.extract_post_call(stream_id, conversation_history)` → dict.
   - **Actualizar BD**: si extracted, `call_repo.update_call_extraction(call_db_id, extracted)` (escribe en Call.extracted_data).
   - **Cerrar llamada**: `call_repo.end_call(call_db_id)`.

El legacy usa conversation_history como lista de dicts `{"role": "user"|"assistant", "content": "..."}` para el servicio de extracción.

---

## 3. Estado actual en V2

- **Orchestrator.stop()**: save_transcripts → end_call; **no** ejecuta extracción ni update_call_extraction.
- **CallPersistencePort**: solo create_call, save_transcripts, end_call; **no** update_call_extraction.
- **client_state / CRM**: V2 no tiene crm_manager ni uso de client_state en el orquestador (queda fuera de alcance Fase 5 salvo anotación).

---

## 4. Brecha de paridad (prioritaria)

| Capacidad | Legacy | V2 actual | Acción |
|-----------|--------|-----------|--------|
| Extracción post-llamada | Sí: extract_post_call → update_call_extraction | No | Añadir port de extracción + update_call_extraction en port de persistencia; orquestador llama extracción antes de end_call. |
| Guardar extracted_data en Call | Sí (JSON) | No | Añadir update_call_extraction al adapter e invocarlo tras extracción. |
| CRM / client_state en stop | Opcional (crm_manager) | No | No implementar en Fase 5; registrar como posible extensión. |

---

## 5. Decisiones para implementación

- **Extracción en V2**: Definir `ExtractionPort` en app_v2 (ej. `extract(stream_id, items: list[tuple[str,str]]) -> dict`). El adapter en app usará `extraction_service.extract_post_call` (convertir items a lista de dicts role/content).
- **Persistencia**: Añadir `update_call_extraction(call_id, extracted_data)` a `CallPersistencePort`; implementar en `V2CallPersistenceAdapter` con `db_service.update_call_extraction`.
- **Orquestador**: Parámetro opcional `extraction_port`. En stop(): tras save_transcripts, si hay extraction_port y persistence_port y call_db_id, llamar extraction_port.extract(stream_id, items), luego persistence_port.update_call_extraction(call_id, extracted), luego end_call. Si extracción falla o devuelve vacío, seguir con end_call sin bloquear.
- **Rutas**: Inyectar el mismo adapter de extracción (en app) en simulador V2 y telephony V2 para paridad en ambos canales.

---

## 6. Fuera de alcance (registro)

- CRM manager y update_status al cierre (si se requiere después, será extensión).
- Uso de client_state dentro del orquestador V2 (hoy solo se pasa por URL en Telnyx; no se usa en stop).
- Schema de extracción configurable por perfil (legacy tiene extraction_schema en perfiles; extraction_service usa schema fijo; paridad con schema fijo en Fase 5).

---

*Documento de revisión para Fase 5. Build Log: Paso 9.*
