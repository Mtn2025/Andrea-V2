"""
Port: CallPersistencePort.

Interface para persistir la llamada en Historial al cierre de sesión:
crear registro al inicio, guardar transcripciones (user/assistant) y cerrar llamada.
El adapter en app escribe en la misma BD que usa el dashboard (calls, transcripts).

Referencia legacy: app/domain/ports/call_repository_port.py, transcript_repository_port.py,
app/core/orchestrator_v2.py (create_call, transcript_repo.save, end_call).
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 6 (Fase 2).
"""

from abc import ABC, abstractmethod


class CallPersistencePort(ABC):
    """
    Port para persistencia de llamada en Historial.

    Uso: orquestador llama create_call al inicio (obtiene call_id),
    al cierre llama save_transcripts con la historia de conversación
    y end_call. app_v2 no conoce BD; el adapter en app implementa con db_service.
    """

    @abstractmethod
    async def create_call(self, stream_id: str, client_type: str) -> int | None:
        """
        Crea el registro de llamada al inicio de la sesión.

        Args:
            stream_id: Identificador único de la sesión (ej. client_id del WebSocket).
            client_type: "browser" | "twilio" | "telnyx".

        Returns:
            ID del registro creado (o existente) o None si falla.
        """
        ...

    @abstractmethod
    async def save_transcripts(
        self,
        call_id: int,
        items: list[tuple[str, str]],
    ) -> None:
        """
        Persiste las transcripciones de la llamada (en orden).

        Args:
            call_id: ID del registro de llamada.
            items: Lista de (role, content) con role "user" o "assistant".
        """
        ...

    @abstractmethod
    async def update_call_extraction(self, call_id: int, extracted_data: dict) -> None:
        """
        Actualiza el registro de llamada con datos extraídos del diálogo (post-llamada).

        Args:
            call_id: ID del registro de llamada.
            extracted_data: Diccionario JSON (summary, intent, sentiment, etc.).
        """
        ...

    @abstractmethod
    async def end_call(self, call_id: int) -> None:
        """
        Marca la llamada como finalizada (end_time, status completed).

        Args:
            call_id: ID del registro de llamada.
        """
        ...
