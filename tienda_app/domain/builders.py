from decimal import Decimal

from ..models import Orden
from .logic import CalculadorImpuestos


class OrdenBuilder:
    """Ensambla una Orden paso a paso (Builder), centralizando el cálculo de
    totales e impuestos y evitando un constructor gigante en el modelo o en
    la vista. Soporta tanto compra de un solo libro (con_libro/con_cantidad,
    usado por Compra Rápida) como una lista de productos (con_productos)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._libro = None
        self._cantidad = 1
        self._items = []
        self._direccion = ""

    def con_usuario(self, usuario):
        self._usuario = usuario
        return self  # Permite Fluent Interface

    def con_libro(self, libro):
        self._libro = libro
        return self

    def con_cantidad(self, cantidad):
        self._cantidad = cantidad
        return self

    def con_productos(self, productos):
        self._items = list(productos)
        return self

    def para_envio(self, direccion):
        self._direccion = direccion
        return self

    def build(self) -> Orden:
        if self._items:
            if not self._usuario:
                raise ValueError("Datos insuficientes para crear la orden.")

            # Encapsulamos la lógica de cálculo
            subtotal = sum(Decimal(str(producto.precio)) for producto in self._items)
            total = subtotal * (Decimal("1") + CalculadorImpuestos.IVA)
            libro = self._items[0]
            cantidad = len(self._items)
        elif self._libro:
            total_unitario = CalculadorImpuestos.obtener_total_con_iva(self._libro.precio)
            total = Decimal(str(total_unitario)) * self._cantidad
            libro = self._libro
            cantidad = self._cantidad
        else:
            raise ValueError("Datos insuficientes para crear la orden.")

        orden = Orden.objects.create(
            usuario=self._usuario,
            libro=libro,
            cantidad=cantidad,
            total=total,
            direccion_envio=self._direccion,
        )
        self.reset()
        return orden
