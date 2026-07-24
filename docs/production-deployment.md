# Despliegue de producción

## Opción gratuita para la API: Render

El repositorio incluye `render.yaml` para crear `iica-api` como servicio web
gratuito. Al importar el Blueprint, Render solicita:

- `DATABASE_URL`: conexión Session pooler de Supabase, cambiando el esquema a
  `postgresql+psycopg://`.
- `SUPABASE_ADMIN_EMAILS`: correos separados por comas autorizados para
  administrar los catálogos.

La URL resultante `https://iica-api.onrender.com` debe guardarse como variable
`IICA_API_URL` del repositorio en GitHub. Las instancias gratuitas pueden
suspenderse por inactividad y tardar en responder en el primer acceso.

El mismo Blueprint publica el panel estático en
`https://iica-admin.onrender.com`. En Supabase Auth, agrega esa URL tanto como
Site URL como en la lista de Redirect URLs para habilitar el enlace mágico.

La arquitectura objetivo usa tres servicios:

- **Cloudflare Pages** publica `apps/web/out` y `apps/admin/out`.
- **Google Cloud Run** ejecuta la imagen definida en `docker/api.Dockerfile`.
- **Supabase** proporciona PostgreSQL y autenticación.

## 1. Supabase

1. Crea un proyecto y conserva su URL, clave pública y cadena PostgreSQL.
2. En Authentication, habilita correo con enlace mágico y correo/contraseña.
3. Añade las URLs públicas de web y administración como Redirect URLs.
4. No expongas la clave `service_role` en Next.js ni en GitHub.
5. La API recibe la URL del proyecto como `SUPABASE_URL` y valida los JWT
   mediante el JWKS público de Supabase.
6. Define `SUPABASE_ADMIN_EMAILS` con los correos autorizados para modificar
   el catálogo.

La migración `0002_evaluation_history` crea el historial de cálculos asociado
al identificador autenticado. Las evaluaciones anónimas no se almacenan.

## 2. Cloud Run

El archivo `cloudbuild.yaml` construye la API, la publica en Artifact Registry
y despliega el servicio `iica-api`.

Antes del primer despliegue:

```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com

gcloud artifacts repositories create iica \
  --repository-format=docker \
  --location=us-east1

printf '%s' "$DATABASE_URL" | gcloud secrets create iica-database-url \
  --data-file=-
```

La cuenta de Cloud Build necesita:

- `roles/run.admin`
- `roles/artifactregistry.writer`
- `roles/iam.serviceAccountUser`
- acceso a `iica-database-url` como Secret Manager Secret Accessor.

Después se ejecuta:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions \
_WEB_ORIGIN=https://web.example.pages.dev,\
_ADMIN_ORIGIN=https://admin.example.pages.dev,\
_SUPABASE_URL=https://project.supabase.co,\
_ADMIN_EMAILS=admin@example.com
```

La API aplica las migraciones Alembic antes de iniciar Uvicorn.

## 3. Cloudflare Pages

Crea dos proyectos conectados al repositorio:

| Proyecto | Comando de compilación            | Directorio publicado |
| -------- | --------------------------------- | -------------------- |
| Web      | `pnpm --filter @iica/web build`   | `apps/web/out`       |
| Admin    | `pnpm --filter @iica/admin build` | `apps/admin/out`     |

Variables de la web:

```text
NEXT_PUBLIC_IICA_API_URL=https://iica-api-....run.app
NEXT_PUBLIC_SUPABASE_URL=https://project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
NEXT_PUBLIC_BASE_PATH=
```

El proyecto administrativo usa las mismas variables, excepto
`NEXT_PUBLIC_BASE_PATH`.

## 4. Datos mínimos antes de habilitar cálculos

El panel o la API administrativa deben cargar:

1. País y ciudad.
2. Marca, modelo y versión.
3. Precio, seguridad, garantía y señales de mercado con URL de fuente.
4. Restricción de movilidad vigente por ciudad y motorización.
5. Medición vigente de infraestructura.
6. Reglas tributarias e incentivos aplicables.

La API responde `422` e identifica el dato faltante en lugar de fabricar una
puntuación.

## 5. GitHub Pages durante la transición

Configura en **Settings → Secrets and variables → Actions → Variables**:

- `IICA_API_URL`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`

Una nueva ejecución de `Deploy web to GitHub Pages` incorporará esas URLs al
sitio estático.
