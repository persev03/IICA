# Base de datos

PostgreSQL es la fuente de verdad para catálogo, territorio y reglas locales.
La migración inicial crea países, departamentos/regiones, ciudades, marcas,
modelos, versiones, impuestos, incentivos, restricciones de movilidad e
infraestructura.

Cada regla que afecta un resultado IICA exige fecha de vigencia y `source_url`.
No deben agregarse valores tributarios ni reglas de circulación de ejemplo.

## Migraciones

Con Python 3.11+ y PostgreSQL disponibles:

```bash
pip install -e 'apps/api[dev]'
DATABASE_URL='postgresql+psycopg://iica:iica@localhost:5432/iica' \
  alembic -c database/alembic.ini upgrade head
```

Los catálogos iniciales permitidos están documentados en
[`seeds`](seeds/README.md).
