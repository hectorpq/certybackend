# Docker

## Backend — `certybackend/Dockerfile`

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y binutils libproj-dev gdal-bin libpq-dev gcc
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
```

- **Base:** Python 3.12-slim
- **Dependencias del sistema:** GDAL + libproj (geo), libpq (PostgreSQL)
- **Servidor:** Gunicorn con 2 workers

## Frontend — `certyfront/Dockerfile`

Multi-etapa:
1. **Builder:** `node:20` — `npm ci && npm run build`
2. **Producción:** `nginx:alpine` sirviendo `dist/`

## Docker Compose — `certybackend/docker-compose.yml`

| Servicio | Imagen | Puerto |
|----------|--------|--------|
| `db` | `postgres:15-alpine` | 5434 |
| `redis` | `redis:7-alpine` | 6379 |
| `web` | build local | 8000 |
| `celery_worker` | build local | — |
| `jenkins` | `jenkins/jenkins:lts-jdk17` | 9080 |
| `sonarqube` | `sonarqube:lts-community` | 9001 |

Red compartida: `certy_network`.

## Comandos Útiles

```bash
# Construir imágenes
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f web celery_worker

# Ejecutar comando en contenedor
docker-compose exec web python manage.py migrate

# Detener
docker-compose down
```
