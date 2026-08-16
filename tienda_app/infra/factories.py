from .gateways import BancoNacionalProcesador


class PaymentFactory:
    """Aísla la creación del procesador de pagos (DIP): la vista y el servicio
    dependen de la abstracción ProcesadorPago, no de esta fábrica concreta."""

    @staticmethod
    def get_processor():
        return BancoNacionalProcesador()
