# Dockerfile ULTRA liviano (Alpine based or Slim)
FROM python:3.11-slim

# Evitar archivos .pyc y buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del worker
COPY . .

# Exponer puerto (Railway usa variable PORT, uvicorn lo lee o se asigna)
ENV PORT=8001
EXPOSE 8001

# Comando para Producción: Correr servidor FastAPI
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}"]
