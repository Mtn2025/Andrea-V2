"""
Adapter V2 para ExtractionPort.

Usa el servicio legacy extraction_service para extraer datos estructurados
del diálogo (summary, intent, sentiment, etc.). Convierte items (role, content)
a la lista de dicts que espera el servicio.

Referencia legacy: app/services/extraction_service.py.
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 9 (Fase 5).
"""

import logging

from app.services.extraction_service import extraction_service
from app_v2.domain.ports import ExtractionPort

logger = logging.getLogger(__name__)


class V2ExtractionAdapter(ExtractionPort):
    """
    Implementación de ExtractionPort usando extraction_service (Groq LLM).
    """

    async def extract(
        self,
        stream_id: str,
        items: list[tuple[str, str]],
    ) -> dict:
        if not items:
            return {}
        history = [{"role": role, "content": content or ""} for role, content in items]
        try:
            return await extraction_service.extract_post_call(stream_id, history)
        except Exception as e:
            logger.warning("V2 extraction failed for stream_id=%s: %s", stream_id, e)
            return {}
