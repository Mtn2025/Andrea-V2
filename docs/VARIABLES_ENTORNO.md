# Variables de entorno — Referencia completa

**Uso**: Coolify / Docker; configurar en el panel de variables del proyecto. No compartir valores entre entornos. Ningún valor sensible debe estar hardcodeado en código.

La aplicación carga la configuración desde `app/core/config.py` (pydantic-settings) y, para la política global de llamadas, desde `app/core/global_call_policy.py` (os.getenv). Los valores por defecto indicados son solo fallback cuando la variable no está definida.

---

## Obligatorias (arranque)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `POSTGRES_USER` | Usuario de PostgreSQL | `postgres` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL (mín. 8 caracteres) | — |
| `ADMIN_API_KEY` | Clave de acceso al panel admin y a endpoints protegidos | — |

Opcional: si se define `DATABASE_URL` completo, puede usarse en lugar de `POSTGRES_*` (se convierte a `postgresql+asyncpg://` si hace falta).

---

## Base de datos (opcionales si usas DATABASE_URL)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `POSTGRES_SERVER` | Host de PostgreSQL | `db` |
| `POSTGRES_PORT` | Puerto | `5432` |
| `POSTGRES_DB` | Nombre de la base de datos | `voice_db` |

---

## Servicios AI (recomendadas para flujo V2)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | API key de Groq (LLM + extracción) | — |
| `GROQ_MODEL` | Modelo LLM principal | `llama-3.3-70b-versatile` |
| `GROQ_EXTRACTION_MODEL` | Modelo para extracción post-llamada | `llama-3.1-8b-instant` |
| `AZURE_SPEECH_KEY` | API key de Azure Speech (TTS/STT) | — |
| `AZURE_SPEECH_REGION` | Región de Azure Speech | `eastus` |

---

## Telefonía (opcionales)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | SID de cuenta Twilio | — |
| `TWILIO_AUTH_TOKEN` | Token de autenticación Twilio | — |
| `TELNYX_API_KEY` | API key de Telnyx | — |
| `TELNYX_PUBLIC_KEY` | Clave pública para validación de webhooks Telnyx | — |
| `TELNYX_API_BASE` | URL base de la API Telnyx | `https://api.telnyx.com/v2` |

---

## Política global de llamadas (V2)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `GLOBAL_STOP_MAX_ERRORS_IN_WINDOW` | Número de errores críticos en ventana para activar paro global | `3` |
| `GLOBAL_STOP_WINDOW_SECONDS` | Ventana de tiempo en segundos | `60` |
| `ADMIN_NOTIFICATION_WEBHOOK_URL` | URL a la que se hace POST cuando se activa el paro global | — |

---

## Infraestructura y seguridad

| Variable | Descripción | Default |
|----------|-------------|---------|
| `REDIS_URL` | URL de Redis (estado, caché) | `redis://redis:6379/0` |
| `APP_ENV` | Entorno (development, test, production) | `development` |
| `DEBUG` | Modo debug (no usar true en producción) | `False` |
| `API_V1_STR` | Prefijo de API v1 | `/api/v1` |

`SESSION_SECRET_KEY`: si no se define, la aplicación puede usar `ADMIN_API_KEY` como fallback para sesiones (definir en producción si se quiere separar).

---

## Health y operación

- **Liveness**: GET `/health` → 200 `{"status": "ok"}` (no comprueba BD/Redis).
- **Readiness**: GET `/api/system/health` → 200 con `status`, `database`, `redis` (comprueba BD y Redis).
- **Reanudar llamadas** tras paro global: POST `/admin/reset-global-stop` con header `X-API-Key: <ADMIN_API_KEY>`.

Logs relevantes: eventos `critical_call_error` y `global_call_stop_activated` (logs estructurados).

---

*Actualizado: Fase 6 (Paso 10). Ver `docs/APP_V2_BUILD_LOG.md` y `COOLIFY_DEPLOY.md`.*
