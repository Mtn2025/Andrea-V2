# Revisión legacy — Fase 3: UI (templates, static, rutas)

**Objetivo de la revisión**: Identificar la estructura de la UI legacy (templates, JS, rutas) para copiarla y adaptarla a la UI V2, con el simulador conectado a `/ws/simulator/v2/stream` y el resto de vistas alineadas al backend V2.

**Fecha de la revisión**: 2026-02-09  
**Fase del plan**: Fase 3 — UI V2 (copiar y adaptar la UI legacy).

---

## 1. Ámbito revisado

| Ruta | Rol |
|------|-----|
| `app/templates/dashboard.html` | Página principal: Alpine.js `x-data="dashboard()"`, inyección de config/voices/styles/models/langs vía `<script id="server-*">`, sidebar de pestañas, panel de configuración, área de contenido con partials. |
| `app/templates/partials/panel_simulator.html` | Panel del simulador: botón Iniciar/Detener, visualizador, transcripción en vivo; usa estado del store (simState, transcripts, etc.). |
| `app/templates/partials/tab_*.html` | Pestañas de contenido (modelo, voz, historial, etc.); incluidos según activeTab. |
| `app/static/js/main.js` | Entrada: Alpine.js, Alpine.data('dashboard', dashboardStore). No tiene prefix de ruta. |
| `app/static/js/dashboard/store.v2.js` | dashboardStore(): mezcla SimulatorMixin, estado de pestañas, configs, catálogos; init() parsea server-config, voices, etc. |
| `app/static/js/dashboard/simulator.v2.js` | SimulatorMixin: startTest() abre WebSocket a **/api/v1/ws/media-stream?client=browser**, envía event 'start' y 'media' (media.payload base64), onmessage maneja type 'audio' (msg.data), 'transcript', 'debug'. |
| `app/routers/dashboard.py` | GET /dashboard: renderiza dashboard.html con config_json, voices_json, styles_json, models_json, langs_json, history; usa get_db, db_service.get_agent_config, cache para voces/estilos/modelos. |
| `app/routers/config_router.py` | API de configuración (perfiles browser/twilio/telnyx); prefix y rutas según configuración del router. |
| `app/routers/history_router.py` | prefix /api/history; listado y detalle de llamadas; usa misma BD (Call, Transcript). |
| `app/main.py` | include_router(dashboard), include_router(history_router), include_router(config_router); sin prefix global para dashboard. |

---

## 2. Hallazgos

### 2.1 Rutas y montaje

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/main.py` | dashboard.router sin prefix; history_router con prefix /api/history; config_router con su prefix. | UI V2 puede vivir en una ruta distinta (ej. /dashboard/v2) que renderice un template propio (dashboard_v2.html) reutilizando la misma lógica de datos o simplificada. |

### 2.2 WebSocket del simulador

| Archivo | Línea | Hallazgo | Relevancia para V2 |
|---------|-------|----------|--------------------|
| `app/static/js/dashboard/simulator.v2.js` | 43-44 | wsUrl = `/api/v1/ws/media-stream?client=browser`. Mensajes: event 'start' con start.streamSid, start.media_format; event 'media' con media.payload (base64), media.track. | Para UI V2 hay que usar wsUrl = `/ws/simulator/v2/stream` (opcional ?client_id=). El backend V2 acepta event 'start', 'media' (media.payload), 'stop'. Formato de mensaje compatible; solo cambia la URL. |
| `app/static/js/dashboard/simulator.v2.js` | 71-99 | Respuestas: msg.type === 'audio' (msg.data), msg.type === 'transcript' (msg.role, msg.text), msg.type === 'debug'. | Backend V2 solo envía type 'audio' con data (base64). No envía transcript en vivo ni debug. La UI V2 puede mostrar solo audio; transcripciones en vivo serían una ampliación posterior. |

### 2.3 Datos inyectados en el dashboard

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/routers/dashboard.py` | Template recibe config_json, voices_json, styles_json, models_json, langs_json, history. Requiere get_agent_config, cache (voces, estilos, modelos), get_recent_calls. | La misma BD y config sirven para V2; se puede reutilizar la misma vista de datos o una simplificada. GET /dashboard/v2 puede usar la misma preparación de contexto y renderizar dashboard_v2.html. |

### 2.4 Estructura del template

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/templates/dashboard.html` | Incluye partials (icons, luego contenido por activeTab). Panel simulador se muestra en una pestaña; store único 'dashboard'. | Copiar dashboard.html a dashboard_v2.html y añadir un flag (script o variable global) para que el JS use la URL del simulador V2. Alternativa: un solo template con variable use_v2 y dos branches en JS. La opción más clara es template y ruta separados para V2. |

---

## 3. Conclusiones

### 3.1 Estrategia de implementación

- **Ruta**: Añadir GET `/dashboard/v2` en el router del dashboard (o en un router dedicado dashboard_v2) que renderice `dashboard_v2.html` con el **mismo contexto** que GET /dashboard (config_json, voices_json, styles_json, models_json, langs_json, history). Así config e historial siguen siendo coherentes con la BD que ya usa el backend V2.
- **Template**: Copiar `dashboard.html` a `dashboard_v2.html`; en el `<head>` o antes de cargar main.js, inyectar `<script>window.USE_V2_SIMULATOR = true;</script>`. Opcional: cambiar título a "Panel V2" y un indicador visual (badge) en la barra lateral.
- **Simulador**: En `simulator.v2.js`, en `startTest()`, si `window.USE_V2_SIMULATOR === true`, usar `wsUrl = \`${protocol}//${window.location.host}/ws/simulator/v2/stream\``; en caso contrario mantener la URL legacy. No duplicar todo el mixin; solo la elección de URL.
- **Config e historial**: Reutilizar las mismas APIs y datos (dashboard prepara history y config desde la misma BD). No hace falta duplicar config_router ni history_router; la UI V2 sigue leyendo /api/history y la config inyectada desde el servidor.

### 3.2 Qué no se replica en Fase 3

- Rediseño visual; nuevas funcionalidades que no existan en legacy.
- Transcripciones en vivo desde el servidor V2 (el backend V2 actual no envía eventos 'transcript'; las transcripciones quedan en BD al cierre). La lista de transcripciones en el panel puede quedar vacía durante la llamada o mostrarse solo al cerrar si se añade un endpoint posterior.

### 3.3 Criterio de cierre

- Existe una ruta clara (ej. /dashboard/v2) que sirve la UI V2.
- Desde esa página, el botón del simulador conecta a `/ws/simulator/v2/stream` y el flujo de audio es 100% V2.
- Config e historial en esa página muestran los mismos datos que el backend V2 (misma BD).

---

## 4. Referencias cruzadas

- Plan: `docs/PLAN_TRABAJO_PRODUCCION.md` — Fase 3.
- Build Log: `docs/APP_V2_BUILD_LOG.md` — Paso 7 (por crear).
- Backend simulador V2: `app/api/routes_simulator_v2.py`, `/ws/simulator/v2/stream`.

---

*Revisión legacy cerrada. Próximo paso: implementar GET /dashboard/v2, dashboard_v2.html y elección de URL en simulator.v2.js; registrar en Build Log.*
