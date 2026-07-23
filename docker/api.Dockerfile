FROM python:3.12-slim

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/workspace/apps/api/src

COPY apps/api apps/api
RUN pip install --no-cache-dir -e "apps/api[dev]"
COPY database database

EXPOSE 8000
CMD ["uvicorn", "presentation.http.main:app", "--host", "0.0.0.0", "--port", "8000"]
