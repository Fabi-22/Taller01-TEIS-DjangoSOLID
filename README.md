# TEIS - DjangoSOLID · Tutorial01: Compra Rápida

Proyecto Django que implementa la funcionalidad de **Compra Rápida** aplicando
principios **SOLID**, **Class-Based Views (CBV)** y un **Service Layer**, según
el tutorial "Evolución de Arquitectura en Django" (TEIS / AdS 2026).

**Autora:** Fabiola Valencia

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
│   └── factories.py          # PaymentFactory (aísla la creación del gateway)
├── api/
│   └── views.py              # CompraAPIView (endpoint JSON que reutiliza el Service Layer)
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
| `/tienda/api/v1/comprar/` | `CompraAPIView` | Endpoint JSON (POST) para procesar una compra |
| `/admin/` | Django Admin | Administración de `Libro`, `Inventario`, `Orden` |

## Evidencia de ejecución (log de auditoría)

`BancoNacionalProcesador.pagar()` (en `infra/gateways.py`) registra cada
transacción exitosa en `pagos_locales_fabiola_valencia.log`, en la raíz del
proyecto. Este archivo se genera automáticamente al realizar compras reales
a través de la vista de Compra Rápida.

## Entregables del tutorial

Según la guía del tutorial, se deben entregar:
1. `pagos_locales_fabiola_valencia.log` — con al menos 3 transacciones registradas.
2. Un documento con el código de `services.py` y `views.py`.
