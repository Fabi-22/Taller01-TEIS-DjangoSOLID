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

Este es el código evaluado en la entrega de Tutorial01: el log de auditoría y
el resumen de `services.py`/`views.py` (ver [`README.md`](README.md)).

## Tutorial02: Patrones Creacionales (Factory Method y Builder)

Sobre esta misma arquitectura, el Tutorial02 optimiza la creación de objetos:

- **Factory Method** (`infra/factories.py`) — `PaymentFactory.get_processor()`
  ya no devuelve siempre `BancoNacionalProcesador`: lee la variable de entorno
  `PAYMENT_PROVIDER` y, si vale `MOCK`, entrega un `MockPaymentProcessor` que
  no cobra de verdad y solo imprime `[DEBUG] Mock Payment: ...`. La vista
  sigue sin saber cuál implementación recibe — sigue dependiendo solo de la
  abstracción `ProcesadorPago` (DIP), pero ahora el comportamiento se puede
  cambiar desde la terminal o desde variables de entorno de Docker, sin tocar
  código.

- **Builder** (`domain/builders.py`) — `OrdenBuilder` se extendió para
  soportar, además del flujo original de un solo libro (`con_libro` +
  `con_cantidad`, usado por Compra Rápida), un flujo de carrito con varios
  productos (`con_productos`), sumando los precios y aplicando el IVA en un
  único lugar. Ambos flujos comparten la misma interfaz fluida
  (`con_usuario().con_productos(...).para_envio(...).build()`), lo que evita
  repetir la lógica de cálculo y validación en cada vista.

- **Service Layer** (`services.py`) — `CompraService.ejecutar_proceso_compra`
  agrega el flujo de compra multi-producto descrito en el tutorial, expuesto
  en `/tienda/api/v1/comprar-carrito/` (`CarritoCompraAPIView`).

Entregables de Tutorial02: captura de consola en modo `MOCK`, código de
`infra/factories.py` y `domain/builders.py`, y la reflexión sobre el
`OrdenBuilder` (ver `README.md`).

## Tutorial03: API REST con Django Rest Framework

De "monolito HTML" a "backend headless": se agrega una capa de API que
**reutiliza la Capa de Servicio existente**, sin duplicar lógica de negocio.

- **Instalación** — se agregó `djangorestframework`, `markdown` y
  `django-filter` a `requirements.txt`, y `'rest_framework'` /
  `'django_filters'` a `INSTALLED_APPS` en `config/settings.py`.

- **Adapter / Serializers** (`api/serializers.py`) — `LibroSerializer`
  (`ModelSerializer`) expone `id`, `titulo`, `precio` y `stock_actual` (una
  `@property` nueva en el modelo `Libro` que delega en `Inventario`, sin
  duplicar el dato). `OrdenInputSerializer` (`Serializer` plano, DTO) valida
  `libro_id` y `direccion_envio` antes de tocar la base de datos.

- **API View / Controlador** (`api/views.py`) — `CompraAPIView` se reescribió
  como `rest_framework.views.APIView`: valida con `OrdenInputSerializer`,
  obtiene el gateway de pago con `PaymentFactory` (Tutorial02) y ejecuta
  `CompraService.ejecutar_compra(...)` — **el mismo método que ya usaba**
  `CompraRapidaView` para las compras por HTML. Responde `201` en éxito,
  `400` si el payload es inválido, `409` si es un error de negocio (ej. sin
  stock) y `500` ante un error inesperado. Se agregó también
  `LibroListAPIView` (`GET /api/v1/libros/`) para poder verificar el
  `stock_actual` por API.

- **Prueba de que HTML y API son la misma lógica** — se agregó
  `stock_actual` a la plantilla `compra_rapida.html` y se corrigió
  `CompraRapidaView.post()` para volver a incluir el libro en el contexto
  tras una compra exitosa (antes solo devolvía el mensaje). Así, comprar por
  `/tienda/api/v1/comprar/` descuenta el mismo `Inventario` que se ve al
  visitar `/tienda/compra-rapida/<id>/` en el navegador, y ambos caminos
  generan la misma entrada en `pagos_locales_fabiola_valencia.log` vía
  `BancoNacionalProcesador` — la prueba de que HTML y API son dos "puertas"
  hacia la misma "habitación" (la Capa de Servicio).

Entregables de Tutorial03: el log de auditoría mostrando una compra hecha
por API, y una captura de un `POST` real a `/api/v1/comprar/` desde la
Browsable API de DRF o Postman (ver `README.md`).
