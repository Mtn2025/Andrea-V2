# Revisión legacy — Fase 1: Políticas de error

**Objetivo de la revisión**: Identificar en el código legacy cómo se manejan los errores críticos, las señales de control (EMERGENCY_STOP) y qué falta respecto a la política definida en `POLITICAS_Y_FLUJOS.md` (disculpa, cierre controlado, paro global, notificación al administrador), para diseñar e implementar la Fase 1 en V2 sin asumir sin base.

**Fecha de la revisión**: 2026-02-09  
**Fase del plan**: Fase 1 — Políticas de error en el core V2.

---

## 1. Ámbito revisado

| Ruta | Rol |
|------|-----|
| `app/core/control_channel.py` | Canal de señales de control (INTERRUPT, CANCEL, PAUSE, RESUME, EMERGENCY_STOP, CLEAR_PIPELINE). Envío y recepción con asyncio.Event y Lock. |
| `app/core/orchestrator_v2.py` | Orquestador legacy: start(), stop(), process_audio(), _control_loop(), manejo de excepciones en carga de config, pipeline, audio manager y process_audio. |
| `docs/POLITICAS_Y_FLUJOS.md` | Definición de política de errores: disculpa breve, cierre inmediato, reintento si posible, paro global y notificación admin si persiste. Estado actual en código. |

---

## 2. Hallazgos

### 2.1 ControlChannel y EMERGENCY_STOP

| Archivo | Hallazgo | Relevancia para V2 |
|---------|----------|--------------------|
| `app/core/control_channel.py` | `ControlSignal.EMERGENCY_STOP` existe; método `send_emergency_stop(reason)`. El canal es por instancia (una por orquestador). No hay concepto de “paro global” compartido entre llamadas. | En V2 no se replica el control channel en esta fase; la detección de error crítico puede ser directa en el orquestador. Para paro global hace falta un estado compartido (módulo, Redis o similar) fuera del orquestador. |
| `app/core/control_channel.py` L72-99 | `send(signal, metadata)` y `wait_for_signal(timeout)` con lock; último mensaje sobrescribe el anterior. | Referencia de diseño; V2 puede tener una señal interna “critical_error” que dispare disculpa + cierre sin implementar un canal asíncrono completo en Fase 1. |

### 2.2 Orquestador legacy: reacción a errores en start()

| Archivo | Líneas | Hallazgo | Relevancia para V2 |
|---------|--------|----------|--------------------|
| `app/core/orchestrator_v2.py` | 173-179 | Config load failure: `logger.error`, `await self.stop()`, `return`. Sin disculpa al usuario. | V2: en start() si falla la config, no hay sesión de audio activa; cerrar y opcionalmente registrar es suficiente. No requiere TTS de disculpa si la llamada no llegó a establecerse. |
| `app/core/orchestrator_v2.py` | 203-206 | Call record creation failure: log error, “Continue even if DB fails”. | V2: decisión de diseño: si no hay persistencia aún, no aplica; cuando la haya, decidir si continuar o no. |
| `app/core/orchestrator_v2.py` | 210-214, 218-223, 226-232, 248-252 | Pipeline build/start, AudioManager start, control loop start: en todos, `logger.error` y `await self.stop()`, `return`. Sin mensaje de disculpa al usuario. | V2: en start() el usuario aún no ha recibido audio; stop() cierra el transport. Para errores durante process_audio (STT/LLM/TTS) sí se debe: 1) intentar disculpa por TTS, 2) cerrar. |

### 2.3 Orquestador legacy: EMERGENCY_STOP en el control loop

| Archivo | Líneas | Hallazgo | Relevancia para V2 |
|---------|--------|----------|--------------------|
| `app/core/orchestrator_v2.py` | 334-337 | Cuando llega `ControlSignal.EMERGENCY_STOP`: se lee `reason` del metadata, se registra con `logger.warning`, se llama `await self.stop()` y se sale del loop. **Solo afecta a esta instancia**; no hay paro global. | V2: EMERGENCY_STOP en legacy es por llamada. La política exige “paro global” cuando el problema persiste; eso requiere estado compartido y comprobación en el punto de aceptación de nuevas llamadas. |

### 2.4 Orquestador legacy: process_audio y errores en el pipeline

| Archivo | Líneas | Hallazgo | Relevancia para V2 |
|---------|--------|----------|--------------------|
| `app/core/orchestrator_v2.py` | 355-390 | `process_audio(payload)`: decodifica base64, encola `AudioFrame` en el pipeline. En excepción: solo `logger.error(f"Error processing audio: {e}")`; **no** se envía disculpa, **no** se cierra la llamada, **no** se dispara paro global. El pipeline procesa en otro flujo; el error puede ocurrir dentro del pipeline (STT/LLM/TTS). | V2: el pipeline.run() es síncrono en el mismo flujo; cualquier excepción en STT, LLM o TTS debe capturarse en el orquestador (o en un wrapper del pipeline), intentar disculpa vía TTS, luego cerrar sesión y, si aplica, notificar y activar paro global según umbral. |

### 2.5 Orquestador legacy: speak_direct (posible vehículo de disculpa)

| Archivo | Líneas | Hallazgo | Relevancia para V2 |
|---------|--------|----------|--------------------|
| `app/core/orchestrator_v2.py` | 454-488 | `speak_direct(text)`: sintetiza y envía audio sin pasar por LLM; usa VoiceConfig y SynthesizeTextUseCase. En excepción: `logger.error(f"speak_direct failed: {e}")` sin cierre ni disculpa alternativa. | V2: la disculpa puede implementarse como “enviar texto fijo por TTS” (equivalente a speak_direct) antes de close(). Necesitamos un método o flujo “apology then close” que use el TTSPort con un texto configurable (ej. “Lo sentimos, hemos tenido un problema. La llamada terminará.”). |

### 2.6 Políticas y flujos — estado declarado

| Documento | Hallazgo | Relevancia para V2 |
|-----------|----------|--------------------|
| `docs/POLITICAS_Y_FLUJOS.md` §2 | Política: (1) disculpa breve + cierre; (2) reintento si posible; (3) si persiste: paro global + notificación admin. Estado en código: EMERGENCY_STOP por llamada; faltan disculpa automática, paro global, notificación. | V2 debe implementar: detección de error crítico → disculpa (TTS) → cierre; contador/estado “error recurrente” → paro global; canal de notificación (log estructurado mínimo + opcional webhook/email); forma de reanudar llamadas (config o endpoint). |

---

## 3. Conclusiones

### 3.1 Qué se toma como referencia

- **Política de errores**: La definida en `POLITICAS_Y_FLUJOS.md` (disculpa, cierre, paro global, notificación) es la fuente de verdad.
- **Detección**: Errores críticos en carga de config, en pipeline (STT, LLM, TTS) o en envío de audio. En legacy solo se registran; en V2 deben disparar el flujo de disculpa + cierre.
- **Disculpa**: Equivalente a “hablar un texto fijo por TTS” (legacy: speak_direct). En V2: usar TTSPort con texto de disculpa configurable (por config o constante) y enviar por transport antes de close().
- **Cierre**: Llamar a `transport.close()` y dejar de procesar; igual que legacy `stop()`.

### 3.2 Qué no se replica en V2 (Fase 1)

- **ControlChannel completo**: No se implementa un canal asíncrono de señales en V2 para Fase 1; la reacción a error es síncrona en el mismo flujo (try/except alrededor de pipeline.run() y start()).
- **FSM y barge-in**: Fuera de alcance de Fase 1; la disculpa se envía sin comprobar estado de conversación.

### 3.3 Qué se añade en V2 (no existe en legacy)

- **Paro global**: Estado compartido (por proceso o Redis) que, cuando está activado, hace que las rutas que aceptan nuevas llamadas (simulador V2, luego telephony) rechacen o cierren de inmediato. Reanudación por config, variable de entorno o endpoint admin.
- **Notificación al administrador**: Al menos log estructurado (JSON o campos fijos) con tipo=critical_error, reason, timestamp, call_id si aplica; opcionalmente webhook o email documentado en config.
- **Error recurrente**: Contador o ventana de tiempo (ej. N errores en M segundos) que dispare paro global + notificación; umbral configurable.

### 3.4 Dudas resueltas o pendientes

- **Texto de disculpa**: Debe ser configurable (i18n o por perfil). Para Fase 1 se puede usar una constante o variable de entorno con texto por defecto; documentar en Build Log.
- **Reintento**: La política dice “reintentar si es posible”. Para Fase 1 se considera fuera de alcance explícito; solo disculpa + cierre + paro global + notificación. El reintento puede ser fase posterior.
- **Dónde vive el estado de paro global**: En app (no en app_v2) para no acoplar V2 a Redis; un módulo o variable en app que las rutas V2 consulten antes de crear orquestador. Documentar en Build Log.

---

## 4. Referencias cruzadas

- Plan de trabajo: `docs/PLAN_TRABAJO_PRODUCCION.md` — Fase 1.
- Política de errores: `docs/POLITICAS_Y_FLUJOS.md` §2.
- Build Log: `docs/APP_V2_BUILD_LOG.md` — Paso 5 (Fase 1) por crear.
- Convenciones de documentación: `docs/CONVENCIONES_DOCUMENTACION.md`.

---

*Revisión legacy cerrada. Próximo paso: implementación Fase 1 en app_v2 y app, con registro en Build Log y actualización de POLITICAS_Y_FLUJOS.md según CONVENCIONES_DOCUMENTACION.md.*
