"""
Adapter V2 para CallPersistencePort.

Escribe en la misma BD que usa el dashboard (calls, transcripts) mediante
db_service. Usado por las rutas V2 (simulador, luego telephony) para
persistir al cierre de sesión.

Referencia legacy: app/adapters/outbound/persistence/sqlalchemy_call_repository.py,
sqlalchemy_transcript_repository.py, app/services/db_service.py.
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 6 (Fase 2).
"""

import logging
from collections.abc import Callable

from app_v2.domain.ports import CallPersistencePort
from app.services.db_service import db_service

logger = logging.getLogger(__name__)


class V2CallPersistenceAdapter(CallPersistencePort):
    """
    Implementación de CallPersistencePort usando db_service y sesiones async.
    """

    def __init__(self, session_factory: Callable) -> None:
        """
        Args:
            session_factory: Factory que devuelve contexto async de sesión
                             (ej. AsyncSessionLocal de app.db.database).
        """
        self._session_factory = session_factory

    async def create_call(self, stream_id: str, client_type: str) -> int | None:
        try:
            async with self._session_factory() as session:
                call_id = await db_service.create_call(
                    session=session,
                    session_id=stream_id,
                    client_type=client_type,
                )
                if call_id:
                    logger.info("V2 call record created: call_id=%s stream_id=%s", call_id, stream_id)
                return call_id
        except Exception as e:
            logger.error("V2 create_call failed: %s", e)
            return None

    async def save_transcripts(
        self,
        call_id: int,
        items: list[tuple[str, str]],
    ) -> None:
        if not items:
            return
        try:
            async with self._session_factory() as session:
                for role, content in items:
                    await db_service.log_transcript(
                        session=session,
                        session_id="",
                        role=role,
                        content=content or "",
                        call_db_id=call_id,
                    )
                logger.info("V2 saved %d transcripts for call_id=%s", len(items), call_id)
        except Exception as e:
            logger.error("V2 save_transcripts failed for call_id=%s: %s", call_id, e)

    async def update_call_extraction(self, call_id: int, extracted_data: dict) -> None:
        try:
            async with self._session_factory() as session:
                await db_service.update_call_extraction(session, call_id, extracted_data)
                logger.info("V2 updated extraction for call_id=%s", call_id)
        except Exception as e:
            logger.error("V2 update_call_extraction failed for call_id=%s: %s", call_id, e)

    async def end_call(self, call_id: int) -> None:
        try:
            async with self._session_factory() as session:
                await db_service.end_call(session, call_id)
                logger.info("V2 call ended: call_id=%s", call_id)
        except Exception as e:
            logger.error("V2 end_call failed for call_id=%s: %s", call_id, e)
