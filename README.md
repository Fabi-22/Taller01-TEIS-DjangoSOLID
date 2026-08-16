# TEIS - DjangoSOLID · Tutorial01 + Tutorial02 + Tutorial03

Proyecto Django que implementa la funcionalidad de **Compra Rápida** aplicando
principios **SOLID**, **Class-Based Views (CBV)**, un **Service Layer**, los
patrones creacionales **Factory Method** y **Builder**, y una capa de **API
REST con Django Rest Framework (DRF)**, según los tutoriales "Evolución de
Arquitectura en Django", "Patrones Creacionales en Django" e "Introducción a
APIs con DRF" (TEIS / AdS 2026). Los tres tutoriales viven en este mismo
repositorio: cada uno evoluciona directamente el código del anterior (misma
arquitectura `domain`/`infra`/`services`/`api`).

**Autora:** Fabiola Valencia

## Evolución de la arquitectura

Este repo corresponde al estado final (Service Layer) del tutorial. La
evolución completa —de función espagueti a CBV y luego a Service Layer,
con las violaciones SOLID señaladas en cada paso— está documentada en
[`EVOLUCION.md`](EVOLUCION.md).

## Arquitectura

La lógica de negocio está desacoplada de la vista y organizada en capas:

```
tienda_app/
├── models.py              # Libro, Inventario, Orden
├── views.py                # CompraRapidaView (CBV) — solo orquesta request/response
├── services.py              # CompraRapidaService — orquesta la compra (Service Layer)
├── urls.py
├── domain/
│   ├── interfaces.py        # ProcesadorPago (contrato abstracto, DIP)
│   ├── logic.py              # CalculadorImpuestos (cálculo del IVA)
│   └── builders.py           # OrdenBuilder (construcción de la Orden)
├── infra/
│   ├── gateways.py           # BancoNacionalProcesador (implementación concreta de pago)
│   └── factories.py          # PaymentFactory + MockPaymentProcessor (Factory Method, Docker-ready vía PAYMENT_PROVIDER)
├── api/
│   ├── serializers.py         # LibroSerializer (Adapter) y OrdenInputSerializer (DTO de entrada)
│   └── views.py               # CompraAPIView (DRF), CarritoCompraAPIView y LibroListAPIView
└── templates/tienda_app/
    └── compra_rapida.html      # ahora también muestra el stock_actual del libro
```

**Principios aplicados:**
- **SRP** — la vista solo maneja HTTP; `CompraRapidaService` orquesta la compra; `CalculadorImpuestos` solo calcula impuestos.
- **OCP** — el cálculo de impuestos está aislado en `CalculadorImpuestos`, no hardcodeado en la vista.
- **DIP** — la vista y el servicio dependen de la abstracción `ProcesadorPago`, no de `BancoNacionalProcesador` directamente; `PaymentFactory` resuelve esa dependencia.

## Requisitos

- Python 3.10+
- Django (ver `requirements.txt`)

## Puesta en marcha

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py shell
```

Dentro del shell, crear datos de prueba:

```python
from tienda_app.models import Libro, Inventario
l = Libro.objects.create(titulo="Clean Code en Python", precio=150.0)
Inventario.objects.create(libro=l, cantidad=10)
```

Luego levantar el servidor:

```bash
python manage.py runserver
```

## Rutas disponibles

| Ruta | Vista | Descripción |
|---|---|---|
| `/tienda/compra-rapida/<libro_id>/` | `CompraRapidaView` | Muestra el detalle del producto (GET) y procesa la compra (POST) |
| `/tienda/compra/<libro_id>/` | `CompraView` | Alias de `CompraRapidaView` |
| `/tienda/api/v1/comprar/` | `CompraAPIView` (DRF) | Endpoint REST (POST) para procesar una compra de un solo libro. Payload: `{"libro_id": 1, "direccion_envio": "Calle 123"}`. Navegable desde el navegador (Browsable API de DRF) o desde Postman |
| `/tienda/api/v1/comprar-carrito/` | `CarritoCompraAPIView` | Endpoint JSON (POST) para procesar una compra con varios productos (`{"libro_ids": [...], "direccion": "..."}`), requiere usuario autenticado |
| `/tienda/api/v1/libros/` | `LibroListAPIView` (DRF) | Endpoint REST (GET) con el catálogo y su `stock_actual`, para verificar por API que el inventario cambió |
| `/admin/` | Django Admin | Administración de `Libro`, `Inventario`, `Orden` |

## Patrones creacionales (Tutorial02)

- **Factory Method** (`infra/factories.py`): `PaymentFactory.get_processor()`
  decide en tiempo de ejecución, según la variable de entorno
  `PAYMENT_PROVIDER`, si entrega `BancoNacionalProcesador` (por defecto) o
  `MockPaymentProcessor` (pruebas, sin cargo real). La vista no sabe cuál se
  usa — solo depende de la abstracción `ProcesadorPago`.

  ```bash
  # Modo producción (banco real)
  python manage.py runserver

  # Modo desarrollo/test (mock, imprime "[DEBUG] Mock Payment...")
  PAYMENT_PROVIDER=MOCK python manage.py runserver
  ```

- **Builder** (`domain/builders.py`): `OrdenBuilder` ensambla la `Orden` paso
  a paso con una interfaz fluida (`con_usuario`, `con_libro`/`con_cantidad`
  para un solo producto, o `con_productos` para un carrito, `para_envio`),
  centralizando el cálculo de subtotal + IVA y la validación de datos
  mínimos antes de crear el registro en base de datos.

## API REST con DRF (Tutorial03)

`CompraAPIView` (`tienda_app/api/views.py`) es un `rest_framework.views.APIView`
que **reutiliza el mismo `CompraService`** que ya usa la vista HTML de Compra
Rápida — la lógica de negocio no se duplica, solo cambia quién la llama
(demuestra que HTML y API son dos "puertas" a la misma "habitación", la Capa
de Servicio):

- **Adapter** (`api/serializers.py`) — `OrdenInputSerializer` valida la
  entrada (`libro_id`, `direccion_envio`) como un DTO; `LibroSerializer`
  transforma `Libro` (incluido `stock_actual`, una propiedad calculada a
  partir de `Inventario`) a JSON.
- **Factory** — igual que en Tutorial02, `PaymentFactory.get_processor()`
  decide el procesador de pago según `PAYMENT_PROVIDER`.
- **Service Layer** — `servicio.ejecutar_compra(...)` es exactamente el
  mismo método que usa `CompraRapidaView`.
- Respuestas: `201` (compra exitosa), `400` (payload inválido), `409`
  (error de negocio, ej. sin stock), `500` (error inesperado).

Para probarlo desde el navegador (Browsable API de DRF) o desde Postman:

```
POST http://127.0.0.1:8000/tienda/api/v1/comprar/
Content-Type: application/json

{"libro_id": 1, "direccion_envio": "Calle 123"}
```

## Evidencia de ejecución (log de auditoría)

`BancoNacionalProcesador.pagar()` (en `infra/gateways.py`) registra cada
transacción exitosa en `pagos_locales_fabiola_valencia.log`, en la raíz del
proyecto. Este archivo se genera automáticamente al realizar compras reales
a través de la vista de Compra Rápida.

## Entregables

**Tutorial01:**
1. `pagos_locales_fabiola_valencia.log` — con al menos 3 transacciones registradas.
2. Un documento con el código de `services.py` y `views.py`.

**Tutorial02:**
1. Captura de consola en modo `PAYMENT_PROVIDER=MOCK` mostrando `[DEBUG] Mock Payment...`.
2. Código de `infra/factories.py` y `domain/builders.py`.
3. Reflexión sobre por qué `OrdenBuilder` reduce el riesgo de errores frente a construir la orden directamente en la vista.

**Tutorial03:**
1. `pagos_locales_fabiola_valencia.log` mostrando que la compra hecha por API también descuenta inventario y genera log (misma lógica que la vista HTML).
2. Captura de pantalla de un `POST` a `/api/v1/comprar/` desde Postman o la Browsable API de DRF.
