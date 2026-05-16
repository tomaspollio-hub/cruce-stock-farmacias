FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema (para pandas/openpyxl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar toda la app
COPY . .

# Directorio de datos persistentes (montado como volumen en producción)
RUN mkdir -p /data/uploads

EXPOSE 8080

CMD ["gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "server.app:app"]
