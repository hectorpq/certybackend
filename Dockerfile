FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils \
    libproj-dev \
    gdal-bin \
    libpq-dev \
    gcc \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

# Workers: 4 procesos + 2 threads cada uno = 8 workers concurrentes.
# Se permite recargar workers tras 1000 requests para evitar memory leaks
# (con jitter para que no recarguen todos a la vez).
# PORT y WEB_CONCURRENCY los define la plataforma (Render usa PORT=10000 y
# WEB_CONCURRENCY=1 en el plan free); en local se usan 8000 y 2 workers.
# createsuperuser --noinput crea el admin desde DJANGO_SUPERUSER_* si existen.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && (python manage.py createsuperuser --noinput || true) && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --threads 2 --timeout 120 --graceful-timeout 30 --max-requests 1000 --max-requests-jitter 50"]
