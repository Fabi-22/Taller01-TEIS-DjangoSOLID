# TEIS - DjangoSOLID · Tutorial01 + Tutorial02

Proyecto Django que implementa la funcionalidad de **Compra Rápida** aplicando
principios **SOLID**, **Class-Based Views (CBV)**, un **Service Layer** y los
patrones creacionales **Factory Method** y **Builder**, según los tutoriales
"Evolución de Arquitectura en Django" y "Patrones Creacionales en Django"
(TEIS / AdS 2026). Ambos tutoriales viven en este mismo repositorio: el
segundo evoluciona directamente el código del primero (misma arquitectura
`domain`/`infra`/`services`).

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
│   └── views.py              # CompraAPIView y CarritoCompraAPIView (endpoints JSON del Service Layer)
└── templates/tienda_app/
    └── compra_rapida.html
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
| `/tienda/api/v1/comprar/` | `CompraAPIView` | Endpoint JSON (POST) para procesar una compra de un solo libro |
| `/tienda/api/v1/comprar-carrito/` | `CarritoCompraAPIView` | Endpoint JSON (POST) para procesar una compra con varios productos (`{"libro_ids": [...], "direccion": "..."}`), requiere usuario autenticado |
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
