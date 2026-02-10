# Confirmación: listo para desplegar en Coolify

**Objetivo**: Verificar que el proyecto está listo para Coolify y que el **Simulador V2** funcionará sin problemas tras configurar las variables obligatorias.

**Traefik**: En Coolify, **Traefik se encarga de todo el enrutamiento externo**. El `docker-compose.yml` del repositorio **no expone ningún puerto al host** (app, db, redis). Comunicación interna por red Docker; acceso público solo vía Traefik. Código limpio y correcto para este entorno.

---

## 1. Requisitos de despliegue (Coolify)

| Requisito | Estado |
|-----------|--------|
| Docker Compose / Dockerfile | ✅ `docker-compose.yml` y `Dockerfile` en raíz; puerto **8000** expuesto. |
| Script de arranque | ✅ `scripts/startup.sh`: espera BD, migraciones Alembic, inicia uvicorn. |
| Health check | ✅ `GET /health` (liveness) y `GET /api/system/health` (readiness, BD + Redis). |
| Puertos en host | ✅ Ninguno: Traefik en Coolify gestiona el acceso; compose sin `ports`. |
| Variables desde entorno | ✅ Sin hardcodear; `app/core/config.py` (pydantic-settings) y `global_call_policy` (os.getenv). |
| Documentación | ✅ [docs/VARIABLES_ENTORNO.md](VARIABLES_ENTORNO.md), [docs/OPERACION.md](OPERACION.md), [COOLIFY_DEPLOY.md](../COOLIFY_DEPLOY.md). |

---

## 2. Variables obligatorias (para que arranque la app)

Configurar en Coolify **Secrets/Env Vars** (no compartir entre entornos):

| Variable | Uso |
|----------|-----|
| `POSTGRES_USER` | Usuario de PostgreSQL (obligatorio en config). |
| `POSTGRES_PASSWORD` | Contraseña (mín. 8 caracteres; no usar valores débiles). |
| `ADMIN_API_KEY` | Acceso al dashboard y a `/admin/reset-global-stop` (obligatorio salvo `APP_ENV=test`). |

Si Coolify inyecta `DATABASE_URL` completo, puede usarse en lugar de `POSTGRES_*`. Para Docker Compose con servicio `db`, típicamente: `POSTGRES_SERVER=db`, `POSTGRES_PORT=5432`, `POSTGRES_DB=voice_db`.

---

## 3. Variables necesarias para que el Simulador V2 funcione bien

Sin estas, la app arranca pero las **llamadas del simulador** fallarán (disculpa + cierre por error de config/servicios):

| Variable | Uso en Simulador V2 |
|----------|----------------------|
| `GROQ_API_KEY` | LLM (Groq) y STT (Whisper vía Groq). |
| `AZURE_SPEECH_KEY` | TTS (voz del asistente). |
| `AZURE_SPEECH_REGION` | Región de Azure Speech (ej. `eastus`). |

Opcionales: `GROQ_MODEL`, `GROQ_EXTRACTION_MODEL` (valores por defecto en config).

---

## 4. Acceso al panel y al Simulador V2

1. **URL del panel V2**: `https://<tu-dominio>/dashboard/v2` (o la que configure Coolify/Traefik).
2. **Primera vez**: Si no hay sesión ni `api_key`, se redirige a **/login**. Introducir el valor de `ADMIN_API_KEY` para entrar. Alternativa: `https://<tu-dominio>/dashboard/v2?api_key=<ADMIN_API_KEY>`.
3. **Simulador**: En el panel V2, pestaña del simulador → **Iniciar** → el navegador conecta por WebSocket a `/ws/simulator/v2/stream`. El backend usa orquestador V2 (config desde BD, persistencia, transcripción en vivo, extracción al cierre). La configuración que se ve y guarda en el dashboard es la que usa el simulador.

---

## 5. Comprobaciones rápidas tras desplegar

| Comprobación | Cómo |
|--------------|------|
| App viva | `GET https://<tu-dominio>/health` → 200 `{"status":"ok"}`. |
| BD y Redis | `GET https://<tu-dominio>/api/system/health` → 200 con `database: "connected"` (y `redis` según configuración). |
| Panel V2 | Abrir `/dashboard/v2`, iniciar sesión con `ADMIN_API_KEY`, comprobar que cargan pestañas (config, historial, simulador). |
| Simulador | En panel V2 → Simulador → Iniciar → hablar; debe haber respuesta de voz y transcripción en vivo. Si faltan `GROQ_API_KEY` o `AZURE_SPEECH_KEY`, la llamada termina con mensaje de disculpa. |

---

## 6. Resumen

- **Despliegue en Coolify**: Listo (Docker Compose, startup, health, documentación, variables desde entorno).
- **Simulador V2**: Funcionará sin problemas siempre que en Coolify estén configuradas las variables **obligatorias** (BD + `ADMIN_API_KEY`) y las **necesarias para el flujo V2** (`GROQ_API_KEY`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`). El resto (telefonía, política global, etc.) está documentado en [VARIABLES_ENTORNO.md](VARIABLES_ENTORNO.md).

*Documento de verificación. Build Log: nota post-Paso 10.*
