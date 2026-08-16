# Evolución de Arquitectura — Tutorial01 (TEIS / AdS 2026)

Este documento registra los tres pasos de evolución que pide el tutorial:
de función desordenada (spaghetti) a arquitectura desacoplada con CBV, SOLID
y Service Layer. El código que corre hoy en este repositorio corresponde al
**Paso 3** (estado final); los pasos 1 y 2 se documentan aquí como evidencia
del proceso de refactorización.

## Paso 1: Punto de partida (FBV Spaghetti)

Función original con múltiples responsabilidades mezcladas: acceso a
inventario, cálculo de impuestos hardcodeado y proceso de pago acoplado al
sistema de archivos.

```python
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Libro, Inventario, Orden

def compra_rapida_fbv(request, libro_id):
    libro = get_object_or_404(Libro, id=libro_id)

    if request.method == 'POST':
        # VIOLACION SRP: Logica de inventario en la vista
        inventario = Inventario.objects.get(libro=libro)
        if inventario.cantidad > 0:
            # VIOLACION OCP: Calculo de negocio hardcoded
            total = float(libro.precio) * 1.19

            # VIOLACION DIP: Proceso de pago acoplado al file system
            with open("pagos_manuales.log", "a") as f:
                f.write(f"[{datetime.datetime.now()}] Pago FBV: ${total}\n")

            inventario.cantidad -= 1
            inventario.save()
            Orden.objects.create(libro=libro, total=total)

            return HttpResponse(f"Compra exitosa: {libro.titulo}")
        else:
            return HttpResponse("Sin stock", status=400)

    total_estimado = float(libro.precio) * 1.19
    return render(request, 'tienda_app/compra_rapida.html', {
        'libro': libro,
        'total': total_estimado
    })
```

**Problemas señalados por el tutorial:**
- **SRP**: la vista gestiona inventario, impuestos y pagos a la vez.
- **OCP**: el 19% de IVA está hardcodeado dentro de la vista.
- **DIP**: el registro de pago escribe directo a un archivo, acoplado a la
  implementación en vez de depender de una abstracción.

## Paso 2: Migración a Class-Based View (CBV)

Se separan los verbos HTTP en métodos `get`/`post`, eliminando los
condicionales de `request.method`. La lógica de negocio aún vive en la
vista, pero ya está mejor organizada.

```python
from django.views import View

class CompraRapidaView(View):
    template_name = 'tienda_app/compra_rapida.html'

    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = float(libro.precio) * 1.19
        return render(request, self.template_name, {
            'libro': libro,
            'total': total
        })

    def post(self, request, libro_id):
        # La logica de negocio aun reside aqui, pero separada del GET
        libro = get_object_or_404(Libro, id=libro_id)
        inv = Inventario.objects.get(libro=libro)
        if inv.cantidad > 0:
            total = float(libro.precio) * 1.19
            # ... proceso de compra ...
            return HttpResponse("Comprado via CBV")
        return HttpResponse("Error", status=400)
```

## Paso 3: Service Layer (estado final del repositorio)

La vista se convierte en un puente delgado (<10 líneas de lógica real) y
toda la orquestación de negocio se extrae a `CompraRapidaService`, que
depende de abstracciones (`ProcesadorPago`) en lugar de implementaciones
concretas — ver [`tienda_app/services.py`](tienda_app/services.py) y
[`tienda_app/views.py`](tienda_app/views.py).

Componentes de apoyo:
- `domain/logic.py` → `CalculadorImpuestos` (aísla el cálculo del IVA, OCP).
- `domain/builders.py` → `OrdenBuilder` (construye la `Orden` paso a paso).
- `domain/interfaces.py` → `ProcesadorPago` (contrato abstracto, DIP).
- `infra/gateways.py` → `BancoNacionalProcesador` (implementación concreta
  del pago, deja evidencia en `pagos_locales_fabiola_valencia.log`).
- `infra/factories.py` → `PaymentFactory` (resuelve la dependencia
  concreta del procesador de pago sin acoplar la vista a ella).

Este es el código evaluado en la entrega: el log de auditoría y el
resumen de `services.py`/`views.py` (ver [`README.md`](README.md)).
