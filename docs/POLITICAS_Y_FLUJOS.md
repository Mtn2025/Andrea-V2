# Políticas y flujos del Asistente de Voz

**Fecha**: 2026-02-09  
**Propósito**: Definir flujo de datos (llamada → historial → externos) y política de errores en llamadas reales.

---

## 1. Flujo de datos: durante vs después de la llamada

### Durante la llamada

- **No** se envía información a fuentes externas (N8N, Baserow, CRMs, etc.) en tiempo real.
- Toda la información se mantiene interna: orquestador, pipeline, estado de conversación, transcripciones en memoria/BD interna.

**Motivo**: Cargar datos a N8N/Baserow durante la llamada no es ni funcional ni apropiado (latencia, acoplamiento, fallos externos afectando la llamada).

### Al final de la llamada

- Se persiste en **Historial** (sección del dashboard) toda la información de la llamada:
  - Características de la llamada (número, duración, proveedor, etc.)
  - Interacciones
  - Transcripciones (usuario y asistente)
  - Metadatos y resultados (ej. extracción post-llamada si aplica)

### Después del historial

- Una vez la llamada está cerrada y registrada en Historial/BD:
  - Los flujos externos (N8N, Baserow, etc.) pueden **procesar** esos datos.
  - El asistente no “empuja” en vivo; los sistemas externos **leen** desde Historial/BD o desde webhooks/APIs que consultan el historial.

**Resumen**: Llamada → cierre → escritura en Historial → luego procesamiento externo. Historial es la fuente de verdad para integraciones.

---

## 2. Política de errores en llamadas reales

Cuando ocurre un error grave (LLM, TTS, STT u otro crítico) en una llamada real:

1. **Si es posible**:  
   - Decir una **disculpa breve** al usuario.  
   - **Cortar la llamada de inmediato** (cierre controlado).

2. **Reintento**:  
   - Si es posible, **reintentar/reanudar la llamada de inmediato** (según tipo de error y capacidad del proveedor).

3. **Si el problema persiste**:  
   - **Paro de emergencia**: detener todas las llamadas siguientes.  
   - **Notificar al administrador de inmediato** (alertas, logs, dashboard o canal definido).

**Estado actual en código**:

- **Legacy** (`app/core/orchestrator_v2.py`): Existe `ControlSignal.EMERGENCY_STOP` y el orquestador reacciona (solo para esa llamada). No hay disculpa automática, paro global ni notificación admin.
- **V2** (Fase 1, 2026-02-09): Implementado en `app_v2` y `app`:
  - **Detección**: Errores en carga de config (start) y en pipeline STT/LLM/TTS (process_audio) se consideran críticos.
  - **Disculpa**: Mensaje configurable `CallConfig.apology_message`; se sintetiza por TTS y se envía antes de cerrar la sesión (`app_v2/application/orchestrator.py`).
  - **Cierre**: Transport.close() tras disculpa (o directamente si falla la disculpa).
  - **Paro global**: Estado en `app/core/global_call_policy.py`; umbral por ventana de tiempo (env: `GLOBAL_STOP_MAX_ERRORS_IN_WINDOW`, `GLOBAL_STOP_WINDOW_SECONDS`). Las rutas V2 comprueban `is_calls_allowed()` antes de aceptar.
  - **Notificación**: Log estructurado en cada error; opcional POST a webhook (`ADMIN_NOTIFICATION_WEBHOOK_URL`).
  - **Reanudación**: `POST /admin/reset-global-stop` (API key) o `reset_global_stop()` en código. Documentación: `docs/APP_V2_BUILD_LOG.md` Paso 5, `docs/REVISION_LEGACY_FASE_1.md`.

**Implementación sugerida** (legacy; en V2 ya aplicada según arriba):

- Detección de error crítico en orquestador/pipeline (LLM/TTS/STT).
- Mensaje de disculpa vía TTS (o grabación predefinida) y cierre de llamada.
- Contador o estado “error recurrente” para activar paro de emergencia **global** (todas las llamadas).
- Canal de notificación a admin (log estructurado, webhook, email, o estado en dashboard).
- Control manual de “reanudar llamadas” tras revisión.

---

## 3. Perfiles y prioridad de auditoría

- **Base**: Perfil **Simulador (navegador)** debe quedar **listo primero**. Es la referencia para los otros dos.
- **Luego**: Perfiles **Telnyx** y **Twilio**, cada uno con sus características propias, construidos sobre la misma base que el simulador.

---

## 4. Fallbacks Google STT/TTS

- Google **no** forma parte de la lista oficial de proveedores del producto; se añadió en el pasado como **fallback** cuando Azure STT/TTS falla.
- **Decisión**: Si es posible y útil, se mantiene como fallback opcional. No es obligatorio usarlo en producción.
- **Recomendación**: Hacer el fallback **configurable** (por ejemplo variable de entorno o flag) para poder activarlo o desactivarlo sin cambiar código. Documentar en configuración que “Google solo se usa como respaldo de Azure si está habilitado”.

---

*Documento alineado con criterios del equipo. Actualizar al cambiar políticas o flujos.*
