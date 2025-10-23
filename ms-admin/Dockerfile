# Usa una imagen base liviana de Python 3.11
FROM python:3.13-slim

# Crea el directorio de trabajo
WORKDIR /app

# Copia solo los archivos necesarios para instalar dependencias
COPY requirements.txt /app/

# Instala dependencias desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . /app

# Define PYTHONPATH (una sola vez)
ENV PYTHONPATH=/app:/app/app

# Expone el puerto interno por defecto (informativo)
EXPOSE 8080

# Inicia el servidor leyendo el puerto de $PORT o usando 8080 por defecto
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info"]
