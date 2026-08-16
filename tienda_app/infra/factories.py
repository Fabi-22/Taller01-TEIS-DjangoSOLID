import os

from ..domain.interfaces import ProcesadorPago
from .gateways import BancoNacionalProcesador


class MockPaymentProcessor(ProcesadorPago):
    """Implementación ligera para pruebas (Mocking): no realiza cargos reales."""

    def pagar(self, monto: float) -> bool:
        print(f"[DEBUG] Mock Payment: Procesando pago de ${monto} sin cargo real.")
        return True


class PaymentFactory:
    """Aísla la creación del procesador de pagos (DIP) y decide cuál usar según
    la configuración del entorno, no del código — la app queda "Docker-Ready",
    inyectando dependencias desde la variable PAYMENT_PROVIDER."""

    @staticmethod
    def get_processor():
        provider = os.getenv("PAYMENT_PROVIDER", "BANCO")

        if provider == "MOCK":
            return MockPaymentProcessor()

        # Por defecto usamos la infraestructura real
        return BancoNacionalProcesador()
