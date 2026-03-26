# ═══════════════════════════════════════════════════════════════════
# Dockerfile — Pipeline Hatch-Amplitude Río Cuncumén / Silala
# Multi-stage build para imagen liviana de producción.
#
# Modos de ejecución:
#   docker compose up pipeline          → Prefect + dashboard
#   docker compose up pipeline-standalone → Python puro (sin Prefect)
#   docker compose up prefect           → Solo dashboard Prefect
# ═══════════════════════════════════════════════════════════════════

# ---------- Stage 1: Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar dependencias del sistema para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

LABEL maintainer="Hidrología BH <cesar.godoy@example.com>"
LABEL description="Pipeline Hatch-Amplitude — Río Cuncumén / Silala"
LABEL version="1.0.0"

# Copiar dependencias compiladas
COPY --from=builder /install /usr/local

WORKDIR /app

# Copiar código fuente
COPY src/ src/
COPY scripts/ scripts/

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PREFECT_HOME=/app/.prefect

# Crear usuario no-root
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser \
    && mkdir -p /app/data/processed /app/.prefect \
    && chown -R appuser:appuser /app

USER appuser

# Verificar instalación
RUN python -c "import prefect; import numpy; import pandas; print('OK')"

# Punto de entrada por defecto: pipeline con Prefect
# Se puede sobrescribir con CMD en docker-compose.yml
ENTRYPOINT ["python"]
CMD ["scripts/prefect_pipeline.py"]
