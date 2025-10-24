# ============================================================================
# Stage 1: Builder - Instalación de dependencias
# ============================================================================
FROM python:3.13-slim AS builder

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Crear y activar entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias de Python (incluyendo gunicorn para producción)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# ============================================================================
# Stage 2: Runtime - Imagen final optimizada
# ============================================================================
FROM python:3.13-slim

# Metadata
LABEL maintainer="Linkly Team"
LABEL description="Frontend web application for Linkly URL shortener"
LABEL version="1.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_PORT=5000 \
    FLASK_DEBUG=False \
    PATH="/opt/venv/bin:$PATH"

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 -s /bin/bash appuser

# Establecer directorio de trabajo
WORKDIR /app

# Copiar entorno virtual del builder
COPY --from=builder /opt/venv /opt/venv

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar al usuario no-root
USER appuser

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, requests; requests.get(f'http://localhost:{os.getenv(\"FLASK_PORT\", \"5000\")}/health', timeout=5)" || exit 1

# Comando por defecto - Usar gunicorn para producción
CMD gunicorn --bind 0.0.0.0:${FLASK_PORT:-5000} --workers 4 --timeout 120 "app:create_app()"