from django.urls import path

from .api.views import CarritoCompraAPIView, CompraAPIView
from .views import CompraRapidaView, CompraView

urlpatterns = [
    path("compra-rapida/<int:libro_id>/", CompraRapidaView.as_view(), name="compra_rapida"),
    path("compra/<int:libro_id>/", CompraView.as_view(), name="finalizar_compra"),
    path("api/v1/comprar/", CompraAPIView.as_view(), name="api_comprar"),
    path("api/v1/comprar-carrito/", CarritoCompraAPIView.as_view(), name="api_comprar_carrito"),
]