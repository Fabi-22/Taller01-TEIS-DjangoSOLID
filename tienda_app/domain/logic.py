from decimal import ROUND_HALF_UP, Decimal


class CalculadorImpuestos:
    """Encapsula el cálculo del IVA para desacoplarlo de la vista (OCP)."""

    IVA = Decimal("0.19")

    @staticmethod
    def obtener_total_con_iva(precio) -> Decimal:
        base = Decimal(str(precio))
        total = base * (Decimal("1") + CalculadorImpuestos.IVA)
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
