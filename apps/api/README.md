# IICA API

API FastAPI para el catálogo y los cálculos IICA futuros.

## Ejecutar

```bash
cp .env.example .env
pip install -e '.[dev]'
uvicorn presentation.http.main:app --reload
```

La documentación OpenAPI se expone en `/docs`. Las rutas de lectura de
catálogo son públicas; las mutaciones bajo `/v1/admin` requieren el encabezado
`X-Admin-API-Key` con el valor de `IICA_ADMIN_API_KEY`.

La clave es una protección de transición para la administración técnica. La
autorización por usuario y rol se conectará mediante Auth.js en los flujos web.
