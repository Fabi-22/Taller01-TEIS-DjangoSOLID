from django.shortcuts import get_object_or_404

from .domain.builders import OrdenBuilder
from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro


class CompraRapidaService:
    """Orquesta la compra rápida sin acoplar la vista a la lógica de negocio."""

    def __init__(self, procesador_pago):
        self.procesador_pago = procesador_pago
        self.builder = OrdenBuilder()

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    def procesar(self, libro_id, cantidad=1, direccion="", usuario=None):
        libro = get_object_or_404(Libro, id=libro_id)
        inventario = get_object_or_404(Inventario, libro=libro)

        if inventario.cantidad < cantidad:
            raise ValueError("No hay existencias suficientes.")

        orden = (
            self.builder
            .con_usuario(usuario)
            .con_libro(libro)
            .con_cantidad(cantidad)
            .para_envio(direccion)
            .build()
        )

        if not self.procesador_pago.pagar(orden.total):
            orden.delete()
            raise ValueError("La transacción fue rechazada.")

        inventario.cantidad -= cantidad
        inventario.save(update_fields=["cantidad"])
        return orden.total


class CompraService(CompraRapidaService):
    """Compatibilidad con el nombre anterior usado por la API."""

    def ejecutar_compra(self, libro_id, cantidad=1, direccion="", usuario=None):
        return self.procesar(libro_id, cantidad=cantidad, direccion=direccion, usuario=usuario)
