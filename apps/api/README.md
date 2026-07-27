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

## Búsqueda de lugares

`POST /v1/places/search` consulta un proveedor Nominatim únicamente cuando la
persona envía el formulario. El proxy identifica IICA ante el proveedor,
conserva en memoria los resultados durante 24 horas y serializa las consultas
externas a un máximo de una cada 1,05 segundos. No ofrece autocompletado.

El proveedor se puede cambiar sin modificar el código mediante
`IICA_GEOCODER_URL`. `IICA_GEOCODER_USER_AGENT` permite ajustar la
identificación y el canal de contacto de la instalación.

## IA moderna asistiva (Qwen local)

`POST /v1/ai/evaluations/explain` genera una explicación en lenguaje natural
basada en el resultado determinista de IICA. La respuesta es asistiva: no
modifica scores ni reemplaza la decisión reproducible del motor.

Configuración recomendada (gratis, local):

```bash
ollama pull qwen2.5:7b-instruct
```

Variables opcionales:

- `IICA_OLLAMA_MODEL` (por defecto `qwen2.5:7b-instruct`)
- `IICA_OLLAMA_CHAT_URL` (por defecto `http://localhost:11434/api/chat`)
- `IICA_OLLAMA_TIMEOUT_SECONDS` (por defecto `25`)
- `IICA_OLLAMA_TEMPERATURE` (por defecto `0.2`)

Cada respuesta queda auditada en la tabla `ai_assistant_records` con prompt,
salida, modelo y trazabilidad de usuario cuando existe sesión autenticada.
