"""
Política global de llamadas: paro de emergencia y notificación al administrador.

Estado en memoria (por proceso): cuando se registran N errores críticos en una
ventana de tiempo, se activa el paro global: no se aceptan nuevas llamadas
hasta reanudación manual (reset). Cada error se registra con log estructurado;
opcionalmente se puede llamar a un webhook de notificación.

Usado por las rutas V2 (simulador, luego telephony) para:
- Comprobar si se aceptan nuevas llamadas (is_calls_allowed).
- Registrar error crítico y, si se supera umbral, activar paro global y notificar.

Referencia: docs/POLITICAS_Y_FLUJOS.md §2, docs/REVISION_LEGACY_FASE_1.md.
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 5 (Fase 1).
"""

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Estado en memoria (módulo)
_calls_allowed: bool = True
_error_timestamps: list[float] = []
_max_errors_in_window: int = int(os.getenv("GLOBAL_STOP_MAX_ERRORS_IN_WINDOW", "3"))
_window_seconds: float = float(os.getenv("GLOBAL_STOP_WINDOW_SECONDS", "60"))
_admin_webhook_url: str = os.getenv("ADMIN_NOTIFICATION_WEBHOOK_URL", "").strip()


def is_calls_allowed() -> bool:
    """
    Indica si se aceptan nuevas llamadas.
    False cuando el paro global está activo.
    """
    return _calls_allowed


def report_critical_error(
    reason: str,
    call_id: str | None = None,
    client_type: str | None = None,
) -> None:
    """
    Registra un error crítico: log estructurado, actualiza ventana de errores
    y, si se supera el umbral, activa paro global y notifica al administrador.
    """
    global _calls_allowed, _error_timestamps

    now = time.time()
    _error_timestamps.append(now)

    # Mantener solo errores dentro de la ventana (actualizar estado global)
    _error_timestamps[:] = [t for t in _error_timestamps if now - t <= _window_seconds]
    count = len(_error_timestamps)

    log_extra: dict[str, Any] = {
        "event": "critical_call_error",
        "reason": reason,
        "call_id": call_id,
        "client_type": client_type,
        "error_count_in_window": count,
        "window_seconds": _window_seconds,
    }
    logger.warning("Critical call error reported", extra=log_extra)

    if count >= _max_errors_in_window:
        _calls_allowed = False
        logger.error(
            "Global call stop activated: %d errors in last %.0fs",
            count,
            _window_seconds,
            extra={**log_extra, "event": "global_call_stop_activated"},
        )
        _notify_admin(reason=reason, call_id=call_id, count=count)


def _notify_admin(
    reason: str,
    call_id: str | None = None,
    count: int = 0,
) -> None:
    """
    Notificación al administrador: log estructurado y, si está configurado,
    POST al webhook.
    """
    payload = {
        "event": "global_call_stop_activated",
        "reason": reason,
        "call_id": call_id,
        "error_count_in_window": count,
    }
    if _admin_webhook_url:
        try:
            import httpx
            with httpx.Client() as client:
                resp = client.post(_admin_webhook_url, json=payload, timeout=5.0)
                if resp.status_code >= 400:
                    logger.warning(
                        "Admin webhook returned %s: %s",
                        resp.status_code,
                        resp.text,
                    )
        except Exception as e:
            logger.warning("Admin webhook request failed: %s", e)


def reset_global_stop() -> None:
    """
    Reanuda la aceptación de llamadas (paro global desactivado).
    Limpia la ventana de errores.
    """
    global _calls_allowed, _error_timestamps
    _calls_allowed = True
    _error_timestamps = []
    logger.info("Global call stop reset; calls allowed again")
