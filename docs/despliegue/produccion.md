# Despliegue a Producción

## Requisitos de Infraestructura

- **Servidor:** Linux (Ubuntu 22.04+)
- **Python:** 3.11+
- **Node.js:** 20 LTS
- **PostgreSQL:** 15+
- **Redis:** 7+
- **Nginx:** Última versión estable
- **Docker:** 24+ (opcional)

## Pasos

### 1. Backend

```bash
cd certybackend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env con valores de producción
# DEBUG=False, ALLOWED_HOSTS=dominio.com, etc.

python manage.py migrate
python manage.py collectstatic --noinput

# Servir con Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Worker Celery
celery -A config worker -l info
```

### 2. Frontend

```bash
cd certyfront
npm ci
npm run build
# Servir dist/ con Nginx
```

### 3. Nginx

```nginx
server {
    listen 80;
    server_name certypro.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name certypro.com;

    root /var/www/certyfront/dist;
    index index.html;

    # SSL config...

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

    location /static/ {
        alias /var/www/certybackend/static/;
    }

    location /media/ {
        alias /var/www/certybackend/media/;
    }
}
```

### 4. Servicios como Systemd

Crear servicios systemd para Gunicorn, Celery Worker y Nginx.

## Verificación Post-Despliegue

- [ ] Health check del backend: `GET /api/me/` retorna 401 (esperado sin auth)
- [ ] Frontend carga correctamente en HTTPS
- [ ] Swagger UI accesible en `/api/docs/`
- [ ] Login funciona
- [ ] Creación de evento y certificado funcional
- [ ] Envío de correo funcional
- [ ] Workers Celery activos
