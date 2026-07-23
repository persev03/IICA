# Contenedores

La composición local incluye la web (`3000`), administración (`3001`), API
(`8000`), PostgreSQL (`5432`) y Redis (`6379`). La API aplica las migraciones
al iniciar, después de que PostgreSQL esté disponible.

```bash
docker compose up --build
```

Consulta [la guía de contenedores](README.md) para detener los servicios.
