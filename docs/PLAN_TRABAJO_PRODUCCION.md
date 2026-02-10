# Plan de trabajo hacia producción — 100% llamadas reales

**Objetivo**: Proyecto completo y 100% funcional en producción, procesando todas las llamadas reales (Simulador, Telnyx, Twilio), con rigor, registros y una UI V2 alineada al backend V2.

**Enfoque**: Modular, fase por fase, con retroalimentación antes de avanzar. Todo lo nuevo se construye desde cero en un entorno limpio, usando el código legacy solo como **referencia** (copiar, reconstruir, corregir o prevenir errores).

### Contexto de despliegue

- **Entorno**: Docker Compose; despliegue en **Coolify**; código cargado por **git push main**.
- **Variables de entorno**: No se comparten entre entornos; cada despliegue define las suyas. **No hardcodear** en código ningún valor que deba venir de variables de entorno (API keys, regiones, modelos, URLs, secretos). La aplicación usa `app/core/config.py` (pydantic-settings) para cargar toda la configuración desde env; los valores por defecto en Settings son solo fallback cuando la variable no está definida.

---

## Metodología de trabajo

### Construir desde cero con legacy como referencia

- **V2 = entorno nuevo y limpio.** No se “parchea” el legacy; se construye (o se copia y se adapta) en `app_v2/` y en las piezas de entrada/UI V2 que se definan.
- **Legacy = referencia.** Permite:
  - **Avanzar**: entender flujos, contratos y decisiones ya tomadas.
  - **Copiar**: llevar lógica o estructuras útiles al nuevo código, adaptándolas.
  - **Construir / Reconstruir**: reimplementar en V2 con contratos claros (ports, DTOs).
  - **Corregir**: evitar en V2 los bugs o desalineaciones ya detectados en legacy.
  - **Prevenir**: no repetir dependencias ocultas ni código muerto.
- Cada pieza nueva (políticas de error, persistencia, transport telephony, UI V2, etc.) se diseña e implementa en el contexto V2; el legacy solo informa, no se mezcla con el código nuevo.

### Alcance de “construir desde cero”: código vs. almacenamiento

- **“Desde cero” se aplica al código**: dominio V2, aplicación V2, adapters V2 y puntos de entrada se construyen (o se copian y adaptan) sin parchear el legacy. Los contratos (ports), el flujo y la implementación son nuevos.
- **Persistencia (Fase 2) — decisión actual**: El **código** de persistencia es desde cero (CallPersistencePort, adapter que implementa el port). El **almacenamiento** elegido es la **misma BD** (tablas `calls`, `transcripts`) que ya usa el legacy, para que un solo Historial muestre todas las llamadas (legacy + V2) y no haya que duplicar UI ni fuentes de verdad.
- **Si en el futuro se exigiera “BD construida desde cero sin intervenir con legacy”**: Sería una decisión de arquitectura distinta. Opciones posibles: (a) esquema o tablas propias para V2 (ej. `calls_v2`, `transcripts_v2`) o BD separada, con UI V2 leyendo solo de ahí; (b) definir un esquema único nuevo y migrar. Esa decisión se tomaría y documentaría en su momento; el port CallPersistencePort sigue siendo válido: solo cambiaría el adapter (por ejemplo, uno que escriba en tablas V2 o en otra BD). Esta nota queda como registro para trazabilidad.

### Regla de certeza

- **Si hay dudas** (contratos, formatos, integraciones, comportamiento esperado):  
  1. **Revisar primero lo que ya está en legacy** (rutas, orquestador, repos, UI, schemas). Hay mucho trabajo e información ahí; es la fuente principal antes de asumir.  
  2. **Investigar en línea** cuando haga falta (APIs de Telnyx/Twilio, mejores prácticas, estándares).  
- **No dar nada por seguro** sin haber revisado el legacy (o documentado explícitamente que no aplica). Antes de implementar un bloque, se hace una revisión breve del código legacy correspondiente y, si aporta, se deja anotado en el Build Log o en el plan.

**Resumen**: Revisar legacy → si sigue la duda, investigar en línea → construir o copiar/adaptar en V2 con esa base. No avanzar en falso sin haber mirado el código existente.

### UI V2

- **La UI se puede copiar y editar** para ajustarse a V2. No se limita a “no tocar”; el objetivo es tener una **UI V2** que:
  - Use las rutas y el backend V2 (ej. simulador conectado a `/ws/simulator/v2/stream`).
  - Muestre config, historial y controles alineados con el modelo y las APIs V2.
- **Estrategia**: Copiar la UI legacy (templates, static, routers) y adaptarla: rutas, URLs, nombres de recursos y datos según lo que exponga el backend V2. La UI actual puede seguir existiendo en paralelo durante la transición.

---

## Estado actual (resumen)

| Área | Estado |
|------|--------|
| **Simulador (navegador)** | Flujo 100% V2 operativo (`/ws/simulator/v2/stream`). Config desde BD, STT/LLM/TTS reales. |
| **Telefonía (Telnyx/Twilio)** | Usa orquestador V2: mismo core que simulador, políticas de error y persistencia; V2TelephonyTransport, TTS mulaw_8k; URL `/api/v1/ws/media-stream` sin cambios. |
| **UI actual (legacy)** | Dashboard, templates, `app/static`, `app/routers` (config, history, dashboard). Existe `simulator.v2.js` / `store.v2.js` pero el simulador sigue apuntando al WS legacy; sirve de base para copiar y adaptar. |
| **Historial (backend)** | BD y repos (call_repo, transcript_repo) usados por legacy; history_router y dashboard muestran datos. |
| **Políticas de error** | Definidas en `POLITICAS_Y_FLUJOS.md`. En código: EMERGENCY_STOP por llamada; faltan disculpa automática, paro global, notificación admin. |
| **V2** | Persistencia, políticas de error y UI V2 completadas. Simulador y telefonía (Telnyx/Twilio) usan Orchestrator V2; Historial unificado. |

---

## Fases del plan

**Antes de cada fase**: Revisar en legacy el código relevante (orquestador, pipeline, repos, UI, webhooks) y anotar hallazgos útiles o diferencias; si hay dudas, investigar en línea. No implementar sin haber revisado lo que ya existe.

---

### Fase 1 — Políticas de error en el core V2

**Revisión legacy previa**: `app/core/orchestrator_v2.py` (EMERGENCY_STOP, manejo de errores), `app/core/control_channel.py`, `docs/POLITICAS_Y_FLUJOS.md`.

**Objetivo**: Que cualquier llamada procesada por V2 (hoy el simulador; luego telephony) cumpla la política de errores: en fallo crítico → disculpa breve → cierre controlado; si persiste → paro global + notificación admin.

**Alcance**:
- Detección de error crítico en el pipeline V2 (STT, LLM, TTS o config).
- Mensaje de disculpa (TTS o audio predefinido) y cierre de la sesión (transport.close).
- Mecanismo de **paro global** (estado compartido o Redis): si se dispara, no aceptar nuevas llamadas hasta reanudación manual/config.
- **Notificación al administrador**: al menos un canal definido (log estructurado + opcional webhook/email/dashboard), documentado en config.
- Documentar en Build Log y en `POLITICAS_Y_FLUJOS.md` lo implementado.

**Fuera de alcance (Fase 1)**: UI V2; persistencia en Historial; migración de Telnyx/Twilio.

**Criterio de cierre**: Una llamada V2 que sufra un error crítico recibe disculpa y cierre; un error recurrente activa paro global y notificación; se puede reanudar llamadas (config o endpoint admin).

**Retroalimentación**: Antes de pasar a Fase 2, validar: comportamiento esperado de disculpa, umbral de “error recurrente” y canal de notificación admin.

---

### Fase 2 — Persistencia al cierre de llamada (Historial) en V2

**Revisión legacy previa**: `app/core/orchestrator_v2.py` (create_call, end_call, transcript_repo.save, update_call_extraction), `app/adapters/outbound/persistence/` (sqlalchemy_call_repository, sqlalchemy_transcript_repository), `app/domain/ports/call_repository_port.py`, `app/services/db_service.py`, modelos de BD en `app/db/models.py`.

**Objetivo**: Que cada llamada procesada por el orquestador V2, al finalizar, persista en la misma BD/Historial que ya usa el dashboard (legacy y luego UI V2).

**Alcance**:
- Definir en V2 el contrato de “cierre de llamada” (puerto o callback): datos mínimos (identificador, duración, transcripciones, metadatos). Diseño desde cero; legacy como referencia.
- Implementar en `app/` (o puente desde app_v2) el adapter que escriba en la misma BD que usa el legacy (call_repo / transcript_repo o equivalente) para que el Historial siga mostrando todas las llamadas.
- Simulador V2: al hacer `stop()` o cierre de WebSocket, ejecutar el flujo de cierre (crear/actualizar llamada, guardar transcripciones, end_call).
- Mantener el flujo “durante la llamada no se envía nada a externos; al final todo a Historial” (`POLITICAS_Y_FLUJOS.md`).

**Fuera de alcance**: Integraciones externas (N8N, Baserow); construcción de UI V2 (va en Fase 3).

**Criterio de cierre**: Una sesión del simulador V2, al cerrar, queda registrada en BD con la información esperada (al menos llamada + transcripciones), visible desde el Historial actual.

**Retroalimentación**: Validar formato de datos a persistir y si la extracción post-llamada (como en legacy) va en esta fase o en una posterior.

---

### Fase 3 — UI V2 (copiar y adaptar la UI legacy)

**Revisión legacy previa**: `app/templates/` (dashboard.html, partials: panel_simulator, tab_*, history_rows), `app/static/js/` (main.js, dashboard/simulator.v2.js, store.v2.js, api.js), `app/routers/dashboard.py`, `app/routers/config_router.py`, `app/routers/history_router.py`. Entender qué rutas y datos usa cada vista.

**Objetivo**: Tener una **UI V2** que use exclusivamente el backend V2 (simulador V2, config e historial alineados con V2), construida copiando y editando la UI legacy para ajustarse a V2.

**Alcance**:
- **Copiar** la UI legacy relevante (templates, CSS, JS, rutas de dashboard/config/historial) a una estructura V2 (ej. prefijo de ruta `/dashboard/v2` o carpeta `templates_v2/` y `static_v2/` o equivalente; decisión según convenga).
- **Simulador V2 en UI**: Conectar el panel del simulador a `/ws/simulator/v2/stream` (y `/ws/simulator/v2/start` si aplica); reutilizar o adaptar la lógica de `simulator.v2.js` / store para que use solo endpoints V2.
- **Config y Historial V2**: Adaptar las vistas de configuración e historial para que consuman las APIs/BD que ya alimenta el backend V2 (misma BD de Historial tras Fase 2; config ya cargada por `load_config_for_call`). Si hace falta, exponer rutas API específicas para UI V2 o reutilizar las existentes que lean la misma BD.
- **Editar solo lo necesario**: Ajustar URLs, nombres, mensajes y datos mostrados para que reflejen “V2”; no rediseño estético salvo que se acuerde.
- Documentar en Build Log qué se copió, qué se editó y cómo se accede a la UI V2.

**Fuera de alcance**: Rediseño completo de look & feel; nuevas funcionalidades de producto que no existan en legacy.

**Criterio de cierre**: Existe una UI V2 accesible (ruta clara); el simulador desde esa UI usa 100% el flujo V2; config e historial en esa UI muestran datos coherentes con el backend V2.

**Retroalimentación**: Definir si UI V2 convive con la actual (dos entradas) o si en algún momento se reemplaza; y ruta o estructura de carpetas preferida para la UI V2.

---

### Fase 4 — Migración de Telefonía (Telnyx / Twilio) al core V2

**Revisión legacy previa**: `app/api/routes_telephony.py` (webhooks, WebSocket, eventos media/start/stop), `app/adapters/telephony/transport.py` (TelephonyTransport, protocol twilio/telnyx), `app/core/voice_ports.py` (audio_mode), formatos de audio (mulaw, sample rate). Documentación o ejemplos de Telnyx/Twilio para streaming si hay dudas.

**Objetivo**: Que las llamadas reales por Telnyx y Twilio se procesen con el mismo core V2 (orquestador, pipeline, políticas, persistencia), cambiando solo el transporte y el formato de audio.

**Alcance**:
- Transport de telephony en V2: adapter que implemente `AudioTransport` sobre el WebSocket de telephony (Telnyx/Twilio), traduciendo formato de audio (ej. mulaw 8k) y eventos (media, stop, etc.). Construir desde cero en app_v2; legacy como referencia.
- Loader de config para `client_type=telnyx` y `client_type=twilio` (perfil/overlay ya en BD; reutilizar `load_config_for_call` con ese client_type).
- Rutas de telephony: en lugar de instanciar `VoiceOrchestratorV2` legacy, instanciar el orquestador V2 con los mismos adapters (STT, LLM, TTS) y el transport de telephony; reutilizar el flujo de persistencia de Fase 2.
- Mantener webhooks actuales (incoming-call, call control) y URL del WebSocket; solo cambiar el “motor” interno a V2.
- TTS en telephony: formato de salida adecuado (ej. mulaw_8k) ya contemplado en AzureTTSAdapter.

**Fuera de alcance**: Nuevas funcionalidades de telephony no existentes en legacy.

**Criterio de cierre**: Una llamada entrante por Telnyx (y otra por Twilio si aplica) se atiende con el orquestador V2, se persiste en Historial al finalizar y cumple las políticas de error de Fase 1.

**Retroalimentación**: Validar prioridad Telnyx vs Twilio y requisitos específicos por proveedor (timeouts, códecs, etc.).

---

### Fase 5 — Paridad y robustez (legacy vs V2)

**Revisión legacy previa**: Listar en legacy todo lo que ocurre al cierre de llamada (extracción, client_state, campañas, etc.) en `app/core/orchestrator_v2.py`, repos y services; comparar con lo implementado en V2.

**Objetivo**: Asegurar que no falte ninguna capacidad crítica del legacy en V2 (extracción post-llamada, identificadores, contexto de campaña, etc.) y que el sistema sea estable.

**Alcance**:
- Revisión de diferencias: qué hace el legacy al cierre (extracción, call_repo.update_call_extraction, client_state, etc.) y replicar en V2 lo necesario para que Historial e integraciones externas sigan funcionando.
- Tests de integración/E2E para al menos un flujo completo por canal (simulador, Telnyx o Twilio).
- Opcional: deprecar el orquestador legacy una vez validado (redirigir todo a V2); mantener código legacy solo si hay motivo claro.

**Fuera de alcance**: Cambios en UI V2 que no sean correcciones o paridad de datos.

**Criterio de cierre**: No hay regresiones funcionales; Historial e integraciones posteriores disponen de los datos necesarios; al menos un E2E automatizado por canal principal.

**Retroalimentación**: Revisar lista de capacidades legacy a igualar y priorizar.

---

### Fase 6 — Preparación para producción (operación y despliegue)

**Revisión legacy previa**: `app/core/config.py`, variables de entorno usadas, `app/main.py` (lifespan, middlewares), cualquier endpoint de health o métricas existente.

**Objetivo**: Sistema listo para desplegar en producción: configuración, secretos, salud, observabilidad y criterios de despliegue.

**Alcance**:
- Configuración y secretos: variables de entorno documentadas (BD, API keys, webhooks, notificación admin); sin hardcodear secretos. Coolify: cada instancia configura sus env; no compartir datos de env entre entornos.
- Health/readiness: endpoints que comprueben BD, Redis (si se usa) y opcionalmente proveedores críticos (STT/TTS/LLM).
- Observabilidad: logs estructurados (inicio/fin de llamada, errores, paro global); métricas básicas que cubran V2.
- Documentación operativa: cómo desplegar, cómo reanudar tras paro global, dónde mirar logs y alertas.
- UI V2 y backend V2 utilizables en un despliegue de prueba con la configuración de producción.

**Fuera de alcance**: Rediseño de UI; nuevas funcionalidades de producto.

**Criterio de cierre**: Un despliegue de prueba en un entorno tipo producción es posible siguiendo la documentación; health y logs permiten operar y reaccionar ante errores.

**Retroalimentación**: Validar entorno objetivo (cloud, on-prem, etc.) y requisitos de compliance o seguridad si los hay.

---

## Resumen visual

| Fase | Enfoque | Resultado esperado |
|------|---------|--------------------|
| **1** | Políticas de error en V2 | Disculpa + cierre; paro global; notificación admin. |
| **2** | Persistencia V2 → Historial | Cierre de llamada V2 escribe en la misma BD que usa la UI. |
| **3** | UI V2 | Copiar y editar UI legacy: simulador → V2, config/historial alineados a V2. |
| **4** | Telefonía sobre V2 | Telnyx/Twilio usan orquestador V2; mismo pipeline y políticas. |
| **5** | Paridad y robustez | Sin regresiones; E2E; paridad con legacy donde importe. |
| **6** | Producción | Config, health, logs, docs de despliegue y operación; UI V2 y backend V2 listos. |

---

## Orden y retroalimentación

- Las fases se ejecutan en orden (1 → 2 → 3 → 4 → 5 → 6).
- **Antes de cada fase**: (1) Revisar el código legacy relevante y, si hay dudas, investigar en línea; (2) Ajustar alcance o criterios según tu retroalimentación.
- **Metodología**: Construir desde cero en entorno limpio (V2), usando legacy como referencia para copiar, reconstruir, corregir o prevenir errores; no asumir sin haber revisado legacy.
- **Objetivo final**: Proyecto completo y 100% funcional en producción para llamadas reales, con backend V2 y UI V2 listos y documentados.

---

---

## Registro de avance

| Fecha | Fase | Nota |
|-------|------|------|
| 2026-02-09 | — | Convenciones de documentación creadas (`docs/CONVENCIONES_DOCUMENTACION.md`). |
| 2026-02-09 | 1 | Revisión legacy documentada (`docs/REVISION_LEGACY_FASE_1.md`). Políticas de error V2 implementadas: disculpa, cierre, paro global, notificación admin, reanudación. Ver `docs/APP_V2_BUILD_LOG.md` Paso 5 y `docs/POLITICAS_Y_FLUJOS.md` §2. |
| 2026-02-09 | 2 | Revisión legacy documentada (`docs/REVISION_LEGACY_FASE_2.md`). Persistencia al cierre en V2: CallPersistencePort, V2CallPersistenceAdapter, create_call en start(), save_transcripts + end_call en stop(). Sesiones del simulador V2 quedan en Historial. Ver `docs/APP_V2_BUILD_LOG.md` Paso 6. |
| 2026-02-09 | 3 | Revisión legacy documentada (`docs/REVISION_LEGACY_FASE_3.md`). UI V2: GET /dashboard/v2, template dashboard_v2.html (copia con flag USE_V2_SIMULATOR), simulador en esa página conecta a /ws/simulator/v2/stream. Config e historial reutilizan mismo contexto y BD. Ver `docs/APP_V2_BUILD_LOG.md` Paso 7. |
| 2026-02-09 | 4 | Revisión legacy documentada (`docs/REVISION_LEGACY_FASE_4.md`). Telefonía V2: V2TelephonyTransport en `app/adapters/telephony/v2_telephony_transport.py`; WebSocket en `routes_telephony.py` usa Orchestrator V2 (ConfigAdapter, Groq STT/LLM, Azure TTS mulaw_8k, persistencia, política de errores). Misma URL y webhooks. Ver `docs/APP_V2_BUILD_LOG.md` Paso 8. |
| 2026-02-09 | 5 | Revisión legacy documentada (`docs/REVISION_LEGACY_FASE_5.md`). Paridad extracción post-llamada: ExtractionPort, update_call_extraction en CallPersistencePort; V2ExtractionAdapter (extraction_service); orquestador ejecuta extracción antes de end_call en stop(). Simulador y telephony V2 inyectan extraction_port. Ver `docs/APP_V2_BUILD_LOG.md` Paso 9. |
| 2026-02-09 | 6 | Revisión legacy documentada (`docs/REVISION_LEGACY_FASE_6.md`). Producción: GET /health (liveness), documentación completa de variables (`docs/VARIABLES_ENTORNO.md`), operación (`docs/OPERACION.md`), actualización COOLIFY_DEPLOY y DEPLOY_CHECKLIST. Ver `docs/APP_V2_BUILD_LOG.md` Paso 10. |

---

*Documento vivo: se actualizará con fechas y decisiones conforme se avance fase por fase.*
