# Contenedores

La composición local incluye la web (`3000`), administración (`3001`), API
(`8000`), PostgreSQL (`5432`), Redis (`6379`) y Ollama (`11434`). La API aplica
las migraciones al iniciar, después de que PostgreSQL esté disponible.

```bash
docker compose up --build
```

Para habilitar la IA moderna asistiva con Qwen en local:

```bash
docker compose exec ollama ollama pull qwen2.5:7b-instruct
```

Luego puedes probar:

`POST /v1/ai/evaluations/explain`

Consulta [la guía de contenedores](README.md) para detener los servicios.
