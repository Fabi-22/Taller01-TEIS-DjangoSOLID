from rest_framework import serializers

from ..models import Libro


class LibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = ["id", "titulo", "precio", "stock_actual"]


class OrdenInputSerializer(serializers.Serializer):
    """Serializer para VALIDAR la entrada de datos, no ligado a un modelo.
    Actúa como un DTO (Data Transfer Object)."""

    libro_id = serializers.IntegerField()
    direccion_envio = serializers.CharField(max_length=200)
    # Validaciones extras aquí si fueran necesarias
