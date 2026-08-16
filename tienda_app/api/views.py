import json

from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from ..infra.factories import PaymentFactory
from ..models import Libro
from ..services import CompraService
from .serializers import LibroSerializer, OrdenInputSerializer


class LibroListAPIView(ListAPIView):
    """GET /api/v1/libros/ — expone el catálogo con su stock_actual, para
    verificar por API que el inventario refleja los cambios de una compra."""

    queryset = Libro.objects.all()
    serializer_class = LibroSerializer


class CompraAPIView(APIView):
    """Endpoint para procesar compras vía JSON, usando DRF.
    POST /api/v1/comprar/
    Payload: {"libro_id": 1, "direccion_envio": "Calle 123"}

    Reutiliza el mismo CompraService que ya usa la vista HTML de Compra
    Rápida: la lógica de negocio no cambia, solo cambia quién la llama.
    """

    def post(self, request):
        # 1. Validación de datos de entrada (Adapter)
        serializer = OrdenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data

        try:
            # 2. Inyección de Dependencias (Factory)
            gateway = PaymentFactory.get_processor()

            # 3. Ejecución de Lógica de Negocio (Service Layer)
            servicio = CompraService(procesador_pago=gateway)
            resultado = servicio.ejecutar_compra(
                libro_id=datos["libro_id"],
                direccion=datos["direccion_envio"],
                usuario=request.user if request.user.is_authenticated else None,
            )

            return Response(
                {"estado": "exito", "mensaje": f"Orden creada. Total: {resultado}"},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            # Errores de negocio (ej: Sin stock)
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            # Errores inesperados
            return Response(
                {"error": "Error interno"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
