"""
Excepciones de la capa de aplicación V2.

Define excepciones que el orquestador lanza para señalar eventos que el
entry point (app) debe manejar: por ejemplo error crítico en llamada,
para que la ruta registre el error, active paro global si aplica y
notifique al administrador.

Referencia: docs/POLITICAS_Y_FLUJOS.md, docs/REVISION_LEGACY_FASE_1.md.
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 5 (Fase 1).
"""


class CriticalCallError(Exception):
    """
    Error crítico durante la llamada (STT, LLM, TTS o pipeline).

    El orquestador V2, tras intentar disculpa y cierre de sesión,
    lanza esta excepción para que el entry point (ruta) registre el
    error, actualice el estado de "error recurrente" y, si aplica,
    active paro global y notificación al administrador.

    Attributes:
        reason: Descripción breve del error (para logs y notificación).
        call_id: Identificador de la sesión si está disponible.
    """

    def __init__(self, reason: str, call_id: str | None = None) -> None:
        self.reason = reason
        self.call_id = call_id
        super().__init__(reason)
