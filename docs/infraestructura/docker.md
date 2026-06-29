# Docker

## Backend (`certybackend/Dockerfile`)

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y binutils libproj-dev gdal-bin libpq-dev gcc
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
CMD python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2
```

- **Base:** Python 3.12-slim
- **Dependencias del sistema:** GDAL + libproj (proyecciones geoespaciales), libpq (PostgreSQL)
- **Servidor:** Gunicorn con 2 workers en puerto 8000

## Frontend (`certyfront/Dockerfile`)

Construcción multi-etapa:

1. **Builder:** `node:20` — `npm ci` + `npm run build`
2. **Producción:** `nginx:alpine` sirviendo `dist/`

## Docker Compose Backend (`certybackend/docker-compose.yml`)

| Servicio | Imagen | Puerto | Propósito |
|----------|--------|--------|-----------|
| `db` | `postgres:15-alpine` | 5434 | Base de datos PostgreSQL |
| `redis` | `redis:7-alpine` | 6379 | Broker de Celery |
| `web` | build local | 8000 | Django + Gunicorn |
| `jenkins` | `jenkins/jenkins:lts-jdk17` | 9080 | CI/CD |
| `sonarqube` | `sonarqube:lts-community` | 9001 | Análisis de código |
| `celery_worker` | build local | — | Worker de Celery |

**Red compartida:** `certy_network` (todos los servicios se comunican internamente).

**Variables de entorno del servicio web:** Cargadas desde `.env`. `DB_HOST=db`, `REDIS_URL=redis://redis:6379/0`.

**Volúmenes:** `db_data` (persistencia PostgreSQL), `jenkins_data` (persistencia Jenkins), `docker.sock` montado para que Jenkins ejecute Docker.

## Uso

```bash
# Iniciar todos los servicios
cd certybackend
docker-compose up -d

# Ver logs
docker-compose logs -f web celery_worker

# Reconstruir después de cambios
docker-compose build web
docker-compose up -d web

# Detener
docker-compose down
```
