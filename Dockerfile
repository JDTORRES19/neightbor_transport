# --- Etapa 1: Constructor (Builder) ---
FROM python:3.12-slim AS builder

WORKDIR /app

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que Python guarde en el búfer la salida estándar (útil para ver logs en tiempo real)
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para compilar ciertas librerías de Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Creamos un "wheel" (binario precocinado) de nuestras dependencias
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# --- Etapa 2: Imagen Final de Producción ---
FROM python:3.12-slim

WORKDIR /app

# Instalar solo la librería en tiempo de ejecución para Postgres (no necesita compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiamos las dependencias compiladas de la etapa anterior
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Instalamos las dependencias desde los wheels locales
RUN pip install --no-cache /wheels/*

# Copiamos el resto del código del proyecto
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]