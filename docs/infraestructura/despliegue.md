# Guía de Despliegue

## Requisitos de Producción

- **Servidor:** Linux (Ubuntu 22.04+ recomendado)
- **Python:** 3.11+
- **Node.js:** 20 LTS
- **Base de datos:** PostgreSQL 15+
- **Cache/Broker:** Redis 7+
- **Servidor web:** Nginx (proxy inverso)
- **Aplicación:** Gunicorn (Django), Nginx (frontend)

## Backend

### 1. Preparar el entorno

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave secreta de Django (generar con `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`) |
| `DEBUG` | `False` en producción |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de PostgreSQL |
| `DB_PASSWORD` | Contraseña de PostgreSQL |
| `DB_HOST` | Host de PostgreSQL |
| `DB_PORT` | Puerto (5432) |
| `REDIS_URL` | URL de Redis (`redis://localhost:6379/0`) |
| `ALLOWED_HOSTS` | Dominios permitidos (separados por coma) |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS (frontend) |
| `SENDGRID_API_KEY` | API key de SendGrid |
| `WHATSAPP_TOKEN` | Token de Meta WhatsApp Cloud API |
| `GOOGLE_CLIENT_ID` | Client ID de Google OAuth |

### 3. Migraciones y estáticos

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Iniciar servicios

```bash
# API
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Worker Celery
celery -A config worker -l info

# Beat Celery (si hay tareas programadas)
celery -A config beat -l info
```

## Frontend

### 1. Configurar

```bash
npm ci
```

Variables de entorno (`.env.production`):

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `VITE_API_URL` | URL base del backend | `https://api.certypro.com` |

### 2. Compilar y servir

```bash
npm run build
# Sirve el directorio dist/ con Nginx
```

### Nginx (frontend)

```nginx
server {
    listen 80;
    server_name certypro.com;
    root /var/www/certyfront/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker (Producción)

```bash
# Backend completo
cd certybackend
docker-compose up -d db redis web celery_worker

# Frontend
docker build -t certyfront ./certyfront
docker run -d -p 80:80 --network certy_network certyfront
```
