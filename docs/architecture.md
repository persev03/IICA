# Arquitectura de IICA

## Decisión

IICA es un monorepo con una separación explícita entre aplicaciones
desplegables y paquetes de negocio reutilizables.

```text
apps/web ──────┐
apps/admin ────┼──> apps/api ───> PostgreSQL / Redis
               │        │
               └──> packages/iica-engine
                         │
                    packages/shared
```

`packages/iica-engine` contiene únicamente reglas de evaluación, entradas y
salidas del índice. No importa frameworks ni clientes de base de datos. La API
adapta datos persistidos al motor y las interfaces presentan sus resultados.

## API con Clean Architecture

La aplicación `apps/api/src` se divide en:

- `domain`: entidades, value objects y contratos puros.
- `application`: casos de uso y puertos.
- `infrastructure`: SQLAlchemy, Redis y proveedores externos.
- `presentation`: endpoints FastAPI y esquemas de transporte.

Las dependencias siempre apuntan hacia el dominio. Por ello, cambiar el
proveedor de datos o añadir una app móvil no modifica el cálculo del IICA.

## Datos regulados por administración

País, ciudad, impuestos, incentivos, devolución de IVA, restricciones de
movilidad e infraestructura se modelarán como datos versionados, con vigencia
temporal y procedencia. Ninguna regla tributaria debe codificarse como un
literal en el motor.

## Decisiones de producto

- La puntuación expone una explicación estructurada: fortalezas, debilidades,
  variables influyentes y recomendaciones.
- La interfaz no mostrará subíndices al usuario final; son artefactos internos
  para trazabilidad y calibración.
- Cada cálculo guardará versión del motor y versión de los datos usados para
  que sea reproducible.
