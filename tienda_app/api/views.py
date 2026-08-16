import json

from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from ..infra.factories import PaymentFactory
from ..models import Libro
from ..services import CompraService


@method_decorator(csrf_exempt, name="dispatch")
class CompraAPIView(View):
    """Endpoint JSON que reutiliza el mismo Service Layer que las vistas web."""

    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido."}, status=400)

        libro_id = payload.get("libro_id")
        if not libro_id:
            return JsonResponse({"error": "libro_id es requerido."}, status=400)

        servicio = CompraService(procesador_pago=PaymentFactory.get_processor())
        try:
            total = servicio.ejecutar_compra(
                libro_id,
                cantidad=payload.get("cantidad", 1),
                direccion=payload.get("direccion", ""),
                usuario=request.user if request.user.is_authenticated else None,
            )
        except ValueError as error:
            return JsonResponse({"error": str(error)}, status=400)

        return JsonResponse({"total": str(total)})


@method_decorator(csrf_exempt, name="dispatch")
class CarritoCompraAPIView(View):
    """Endpoint JSON para comprar un carrito con varios productos a la vez,
    ejercitando CompraService.ejecutar_proceso_compra (Builder multi-producto)."""

    def post(self, request):
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido."}, status=400)

        libro_ids = payload.get("libro_ids") or []
        if not libro_ids:
            return JsonResponse({"error": "libro_ids es requerido."}, status=400)

        productos = list(Libro.objects.filter(id__in=libro_ids))
        if not productos:
            return JsonResponse({"error": "No se encontraron productos."}, status=404)

        usuario = request.user if request.user.is_authenticated else None
        servicio = CompraService(procesador_pago=PaymentFactory.get_processor())
        try:
            mensaje = servicio.ejecutar_proceso_compra(
                usuario, productos, payload.get("direccion", "")
            )
        except Exception as error:
            return JsonResponse({"error": str(error)}, status=400)

        return JsonResponse({"mensaje": mensaje})
