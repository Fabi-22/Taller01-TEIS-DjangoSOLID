from django.shortcuts import render
from django.views import View

from .infra.factories import PaymentFactory
from .services import CompraRapidaService


class CompraRapidaView(View):
    template_name = "tienda_app/compra_rapida.html"

    def setup_service(self):
        return CompraRapidaService(procesador_pago=PaymentFactory.get_processor())

    def get(self, request, libro_id):
        contexto = self.setup_service().obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        try:
            total = self.setup_service().procesar(
                libro_id,
                cantidad=1,
                usuario=request.user if request.user.is_authenticated else None,
            )
            contexto = self.setup_service().obtener_detalle_producto(libro_id)
            contexto["mensaje_exito"] = f"Compra exitosa. Total: ${total}"
            return render(request, self.template_name, contexto)
        except ValueError as error:
            contexto = self.setup_service().obtener_detalle_producto(libro_id)
            contexto["error"] = str(error)
            return render(request, self.template_name, contexto, status=400)


class CompraView(CompraRapidaView):
    pass
