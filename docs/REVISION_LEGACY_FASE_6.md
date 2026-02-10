# Revisión legacy — Fase 6: Preparación para producción

**Fecha**: 2026-02-09  
**Objetivo**: Revisar config, health, main, variables de entorno y documentación existente para cerrar Fase 6 (producción) con rigor y registros.

---

## 1. Código revisado

| Archivo | Relevancia |
|---------|------------|
| `app/core/config.py` | Settings (pydantic-settings); todas las variables desde env; validadores POSTGRES_*, ADMIN_API_KEY, AI keys. |
| `app/main.py` | lifespan: configure_logging, redis, http_client, migraciones, create_all; middlewares; rutas; no expone secretos. |
| `app/routers/system.py` | GET /api/system/health: comprueba BD (SELECT 1) y Redis (ping); status healthy/unhealthy/degraded. |
| `app/core/global_call_policy.py` | GLOBAL_STOP_MAX_ERRORS_IN_WINDOW, GLOBAL_STOP_WINDOW_SECONDS, ADMIN_NOTIFICATION_WEBHOOK_URL vía os.getenv. |
| `COOLIFY_DEPLOY.md` | Guía Coolify; listado parcial de env (POSTGRES_*, TELNYX, GROQ, AZURE, ADMIN_API_KEY). |
| `.env.example` | Template amplio; no incluye GROQ_EXTRACTION_MODEL, GLOBAL_STOP_*, ADMIN_NOTIFICATION_WEBHOOK_URL, SESSION_SECRET_KEY. |
| `DEPLOY_CHECKLIST.md` | Menciona GET /health (ruta real es /api/system/health); checklist de migraciones y rollback. |

---

## 2. Hallazgos

### Health
- **Ruta real**: GET **/api/system/health** (prefix del router: /api/system). Retorna JSON con status, database, redis; 200 siempre (status "unhealthy" o "degraded" en cuerpo).
- **Liveness simple**: No existe GET /health a nivel raíz; Coolify puede necesitar una ruta corta para liveness (sin BD). Opción: añadir GET /health que responda 200 {"status": "ok"} para liveness; readiness seguir siendo /api/system/health.

### Configuración
- Toda la config de aplicación pasa por `app/core/config.py` (Settings). Política global usa `os.getenv` para sus tres variables; coherente con “no hardcodear”.
- Variables no documentadas en .env.example ni COOLIFY_DEPLOY: GROQ_EXTRACTION_MODEL, GLOBAL_STOP_MAX_ERRORS_IN_WINDOW, GLOBAL_STOP_WINDOW_SECONDS, ADMIN_NOTIFICATION_WEBHOOK_URL. SESSION_SECRET_KEY se usa en main (fallback a ADMIN_API_KEY si no existe); no está en Settings.

### Logs
- configure_logging() en lifespan; secure_logger; global_call_policy registra con event "critical_call_error" y "global_call_stop_activated". Métricas HTTP en middleware (Prometheus-style).

### Despliegue
- Docker Compose, Coolify, git push main; variables por entorno sin compartir. Documentación operativa (reanudar paro global, health) repartida o incompleta.

---

## 3. Decisiones para Fase 6

- **Documentación de variables**: Crear `docs/VARIABLES_ENTORNO.md` con lista completa (config + global_call_policy), descripción y si son obligatorias/opcionales; enlazar desde COOLIFY_DEPLOY y Build Log.
- **Health**: Mantener /api/system/health como readiness (BD + Redis). Añadir GET /health en raíz (liveness) que responda 200 {"status": "ok"} sin depender de BD, para que Coolify pueda usarlo como probe de vida.
- **COOLIFY_DEPLOY / .env.example**: Actualizar con enlace a VARIABLES_ENTORNO.md y mencionar variables de política (GLOBAL_STOP_*, ADMIN_NOTIFICATION_WEBHOOK_URL) y GROQ_EXTRACTION_MODEL.
- **Operación**: Añadir sección en documentación operativa: reanudar llamadas tras paro global (POST /admin/reset-global-stop), comprobar salud (GET /api/system/health), dónde mirar logs (eventos critical_call_error, global_call_stop_activated).
- **Sin cambios de código críticos**: Config y health ya están alineados con “todo desde env” y comprobación de BD/Redis; solo añadir ruta /health y documentación.

---

*Documento de revisión para Fase 6. Build Log: Paso 10.*
