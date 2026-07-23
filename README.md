# IICA · Índice Inteligente de Compra de Automóviles

IICA determina qué vehículo es más conveniente para una persona específica,
en un lugar y momento determinados. Su salida es un único índice explicable de
0 a 100; no una opinión genérica sobre cuál automóvil es “el mejor”.

## Estado

Se completaron las fases de **arquitectura**, **modelo de dominio**,
**persistencia** y **API**. El repositorio contiene un monorepo preparado para
la web, API, panel administrativo, motor reutilizable, migraciones PostgreSQL,
contratos OpenAPI y documentación de decisión técnica. La landing de
`apps/web` es una primera expresión de producto, no un cálculo real del
índice.

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

La API se ejecutará con Python 3.11+ cuando se implemente la Fase 4:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn src.presentation.http.main:app --reload
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

## Principios

- Un solo índice IICA, siempre personalizado y explicable.
- Las reglas locales y beneficios vigentes son datos administrables; no
  constantes incrustadas en código.
- El dominio no depende de Next.js, FastAPI, SQLAlchemy ni PostgreSQL.
