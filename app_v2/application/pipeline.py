"""
Pipeline V2 — Cadena lineal de procesadores.

Ejecuta un frame a través de cada procesador en orden; el resultado de uno
es la entrada del siguiente. Sin cola, sin prioridades, sin backpressure en Fase 2.

Opcional: on_frame(frame) se invoca después de cada paso con el frame resultante,
para permitir emisión en vivo (ej. transcripción en el panel del simulador).
"""

from collections.abc import Awaitable, Callable

from app_v2.application.frames import Frame
from app_v2.application.processor import Processor


class Pipeline:
    """
    Pipeline lineal: lista de procesadores ejecutados en secuencia.
    """

    def __init__(self, processors: list[Processor]) -> None:
        self._processors = processors

    async def run(
        self,
        frame: Frame,
        on_frame: Callable[[Frame], Awaitable[None]] | None = None,
    ) -> Frame | None:
        """
        Ejecuta el frame a través de todos los procesadores.

        Args:
            frame: Frame inicial (normalmente AudioFrame).
            on_frame: Opcional; se llama con el frame resultante tras cada paso
                      (para emitir transcripción en vivo u otro log).

        Returns:
            Último frame producido, o None si algún procesador devolvió None.
        """
        current: Frame | None = frame
        for processor in self._processors:
            if current is None:
                return None
            current = await processor.process(current)
            if current is not None and on_frame is not None:
                await on_frame(current)
        return current
