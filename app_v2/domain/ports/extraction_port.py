"""
Port: ExtractionPort.

Interface para extracción post-llamada: a partir del historial de conversación
(user/assistant) se obtiene un diccionario estructurado (resumen, intención,
sentimiento, entidades, etc.). El adapter en app puede usar el servicio legacy
(extraction_service) u otra implementación.

Referencia legacy: app/services/extraction_service.py (extract_post_call).
Build Log: docs/APP_V2_BUILD_LOG.md — Paso 9 (Fase 5).
"""

from abc import ABC, abstractmethod


class ExtractionPort(ABC):
    """
    Port para extracción de datos estructurados a partir del diálogo.
    """

    @abstractmethod
    async def extract(
        self,
        stream_id: str,
        items: list[tuple[str, str]],
    ) -> dict:
        """
        Analiza el historial y devuelve datos estructurados (summary, intent, etc.).

        Args:
            stream_id: Identificador de la sesión (para logs).
            items: Lista de (role, content) con role "user" o "assistant".

        Returns:
            Diccionario con campos extraídos (p. ej. summary, intent, sentiment,
            extracted_entities, next_action). Vacío {} si falla o no hay datos.
        """
        ...
