from django.conf import settings
from django.db import models


class Libro(models.Model):
    titulo = models.CharField(max_length=200)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.titulo

    @property
    def stock_actual(self):
        """Campo calculado: delega en Inventario, no duplica el dato."""
        inventario = getattr(self, "inventario", None)
        return inventario.cantidad if inventario else 0


class Inventario(models.Model):
    libro = models.OneToOneField(Libro, on_delete=models.CASCADE, related_name="inventario")
    cantidad = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.libro.titulo} ({self.cantidad})"


class Orden(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    direccion_envio = models.CharField(max_length=255, blank=True, default="")
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        descripcion = self.libro.titulo if self.libro else f"{self.cantidad} producto(s)"
        return f"Orden #{self.pk} - {descripcion}"
