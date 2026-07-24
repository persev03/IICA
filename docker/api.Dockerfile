FROM python:3.12-slim

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/workspace/apps/api/src

COPY packages/iica-engine packages/iica-engine
COPY apps/api apps/api
RUN pip install --no-cache-dir packages/iica-engine apps/api
COPY database database

EXPOSE 8000
CMD ["sh", "-c", "alembic -c database/alembic.ini upgrade head && uvicorn presentation.http.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
