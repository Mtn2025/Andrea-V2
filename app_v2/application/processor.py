"""
Processor V2 — Interface de un eslabón del pipeline.

Cada procesador recibe un Frame y devuelve el siguiente (o None para descartar).
Pipeline ejecuta los procesadores en secuencia.

Referencia legacy: app/core/processor.py (FrameProcessor, process_frame).
Decisión: Método único process(frame) -> Frame | None; sin dirección UPSTREAM/DOWNSTREAM en Fase 2.
"""

from abc import ABC, abstractmethod

from app_v2.application.frames import Frame


class Processor(ABC):
    """
    Procesador de un frame: transforma o enruta al siguiente.

    Implementaciones: STTProcessor, LLMProcessor, TTSProcessor.
    """

    @abstractmethod
    async def process(self, frame: Frame) -> Frame | None:
        """
        Procesa el frame y devuelve el siguiente.

        Args:
            frame: Frame de entrada (AudioFrame o TextFrame según el procesador).

        Returns:
            Siguiente frame para la cadena, o None si se descarta.
        """
        ...
