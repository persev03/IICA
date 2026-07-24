# IICA · Índice Inteligente de Compra de Automóviles

IICA determina qué vehículo es más conveniente para una persona específica,
en un lugar y momento determinados. Su salida es un único índice explicable de
0 a 100; no una opinión genérica sobre cuál automóvil es “el mejor”.

## Estado

El repositorio incluye la web, el panel administrativo, la API FastAPI, el
motor determinista, migraciones PostgreSQL, autenticación con Supabase y
configuración para desplegar la API en Cloud Run. La calculadora solicita
versiones del catálogo y solo produce un resultado cuando existen datos
vigentes y trazables.

## Estructura

```
apps/       Aplicaciones desplegables (web, api, admin)
packages/   Código reutilizable (motor IICA, tipos compartidos, UI)
database/   Migraciones y datos semilla (próxima fase)
docs/       Arquitectura y decisiones técnicas
docker/     Configuración de desarrollo local
```

Consulta [la arquitectura](docs/architecture.md) y el
[plan de fases](docs/roadmap.md) antes de incorporar funcionalidades.

## Inicio rápido

### Web

```bash
pnpm install
pnpm dev
```

Abre [http://localhost:3000](http://localhost:3000).

### API

La API se ejecuta con Python 3.11+:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ../../packages/iica-engine -e '.[dev]'
PYTHONPATH=src uvicorn presentation.http.main:app --reload
```

La documentación interactiva estará en [http://localhost:8000/docs](http://localhost:8000/docs).

## Calidad

```bash
pnpm lint
pnpm test
pnpm build
pnpm format:check
```

## Desarrollo con contenedores

```bash
docker compose up --build
```

Consulta [la guía de contenedores](docker/README.md) para los servicios y
puertos disponibles.

Consulta [el despliegue de producción](docs/production-deployment.md) para
Cloudflare Pages, Cloud Run y Supabase.

## Principios

- Un solo índice IICA, siempre personalizado y explicable.
- Las reglas locales y beneficios vigentes son datos administrables; no
  constantes incrustadas en código.
- El dominio no depende de Next.js, FastAPI, SQLAlchemy ni PostgreSQL.
