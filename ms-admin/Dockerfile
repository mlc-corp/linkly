# Usa una imagen base liviana de Python 3.11
FROM python:3.11-slim

# Crea el directorio de trabajo
WORKDIR /app

# Copia solo los archivos necesarios para instalar dependencias
COPY requirements.txt /app/

# Instala dependencias desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . /app

# Define variable de entorno para que Python encuentre tus módulos
ENV PYTHONPATH=/app

ENV PYTHONPATH=/app:/app/app

# Expone el puerto donde correrá FastAPI
EXPOSE 8080

# Comando por defecto para iniciar el servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
