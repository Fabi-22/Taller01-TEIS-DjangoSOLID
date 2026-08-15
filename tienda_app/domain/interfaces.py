from abc import ABC, abstractmethod


class ProcesadorPago(ABC):
    """Contrato para cualquier procesador de pagos."""

    @abstractmethod
    def pagar(self, monto: float) -> bool:
        raise NotImplementedError