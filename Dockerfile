# ═══════════════════════════════════════════════════════════════════
# Dockerfile — Pipeline Hatch-Amplitude Río Cuncumén / Silala
# Multi-stage build para imagen liviana de producción.
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
COPY data/ data/

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

# Punto de entrada: pipeline con Prefect
ENTRYPOINT ["python", "scripts/prefect_pipeline.py"]
