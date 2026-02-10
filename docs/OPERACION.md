# Operación en producción

Resumen de cómo comprobar salud, reanudar llamadas tras paro global y dónde mirar logs. Entorno: Docker Compose / Coolify; despliegue por git push main.

---

## Health

| Ruta | Uso | Respuesta |
|------|-----|-----------|
| GET `/health` | Liveness (probe de vida; no depende de BD) | 200 `{"status": "ok"}` |
| GET `/api/system/health` | Readiness (BD + Redis) | 200 JSON con `status`, `database`, `redis` |

En Coolify se puede usar `/health` para liveness y `/api/system/health` para readiness. Si la BD o Redis fallan, `/api/system/health` devuelve igualmente 200 pero con `"status": "unhealthy"` o `"degraded"` en el cuerpo.

---

## Paro global de llamadas (V2)

Cuando se registran varios errores críticos en ventana, el sistema activa un **paro global**: no se aceptan nuevas llamadas hasta reanudación manual.

- **Reanudar**: `POST /admin/reset-global-stop` con header `X-API-Key: <ADMIN_API_KEY>`.
- **Configuración**: variables `GLOBAL_STOP_MAX_ERRORS_IN_WINDOW`, `GLOBAL_STOP_WINDOW_SECONDS`, `ADMIN_NOTIFICATION_WEBHOOK_URL` (ver `docs/VARIABLES_ENTORNO.md`).

---

## Logs

- Inicio/cierre de llamada y errores: logs de la aplicación (stdout/stderr en el contenedor).
- Eventos estructurados de política: `critical_call_error`, `global_call_stop_activated` (incluyen reason, call_id, error_count_in_window).
- Notificación al administrador: si está configurado `ADMIN_NOTIFICATION_WEBHOOK_URL`, al activarse el paro global se envía un POST a esa URL.

---

## Variables de entorno

Listado completo y descripción: **`docs/VARIABLES_ENTORNO.md`**. No hardcodear en código; configurar en Coolify (o .env en despliegue manual) por entorno.

---

*Fase 6. Build Log: Paso 10.*
