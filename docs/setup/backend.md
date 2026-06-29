# Instalación del Backend

## Requisitos del Entorno

- Python 3.11 o superior
- PostgreSQL 14+
- Redis (para Celery)
- pip (gestor de paquetes de Python)

## Configuración del Entorno Virtual

```bash
# Clonar el repositorio y acceder al directorio del backend
cd certybackend

# Crear entorno virtual
python -m venv .venv

# Activar el entorno virtual (Windows)
.venv\Scripts\activate

# Activar el entorno virtual (Linux/Mac)
source .venv/bin/activate
```

## Instalación de Dependencias

```bash
pip install -r requirements.txt
```

## Variables de Entorno

Copiar el archivo de ejemplo y editarlo:

```bash
cp .env.example .env
```

### Diccionario Técnico de Variables

| Variable | Descripción |
|----------|-------------|
| `DB_NAME` | Nombre de la base de datos PostgreSQL (`certificados_db` por defecto). |
| `DB_USER` | Usuario de la base de datos PostgreSQL. |
| `DB_PASSWORD` | Contraseña del usuario de PostgreSQL. |
| `DB_HOST` | Host de PostgreSQL (`localhost` en desarrollo). |
| `DB_PORT` | Puerto de PostgreSQL (`5432` por defecto). |
| `SECRET_KEY` | Clave secreta de Django. Generar con: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` para desarrollo, `False` para producción. |
| `SENDGRID_API_KEY` | API Key de SendGrid para envío de correos transaccionales. |
| `DEFAULT_FROM_EMAIL` | Dirección remitente para los correos (`noreply@certypro.app` por defecto). |
| `META_WHATSAPP_TOKEN` | Token de acceso a Meta WhatsApp Cloud API. |
| `META_WHATSAPP_PHONE_ID` | ID del número de teléfono en Meta WhatsApp Cloud API. |
| `GOOGLE_CLIENT_ID` | Client ID de Google OAuth2 (Google Cloud Console). |
| `CERTIFICATE_EXPIRY_DAYS` | Días de validez de los certificados (`365` por defecto). |
| `CERTIFICATE_VERIFICATION_ENABLED` | Habilita la verificación pública de certificados. |
| `REDIS_URL` | URL de conexión a Redis (`redis://localhost:6379/0` por defecto). Usado por Celery como broker. |
| `ALLOWED_HOSTS` | Hosts permitidos separados por coma (producción). |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables para CSRF (producción). |
| `CORS_ALLOWED_ORIGINS` | Orígenes permitidos para CORS (`http://localhost:3000,http://localhost:5173`). |
| `FRONTEND_URL` | URL del frontend para enlaces en correos (`http://localhost:5173`). |
| `CERTIFICATE_VERIFY_BASE_URL` | URL base para códigos QR de verificación (`http://localhost:8000`). |

## Migraciones y Base de Datos

```bash
# Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE certificados_db;"
psql -U postgres -c "CREATE USER certificados_user WITH PASSWORD 'secure_password_here';"
psql -U postgres -c "ALTER ROLE certificados_user SET client_encoding TO 'utf8';"
psql -U postgres -c "ALTER ROLE certificados_user SET default_transaction_isolation TO 'read committed';"
psql -U postgres -c "ALTER ROLE certificados_user SET timezone TO 'UTC';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE certificados_db TO certificados_user;"

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# (Opcional) Cargar datos de ejemplo
python manage.py loaddata fixtures/seed.json
```

## Ejecutar el Servidor Local

```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`.

## Workers de Celery

Para el procesamiento asíncrono de certificados y envío de notificaciones, iniciar Redis y Celery:

```bash
# Terminal 1: Iniciar Redis (Windows con WSL o Redis oficial para Windows)
redis-server

# Terminal 2: Iniciar Celery Worker
celery -A config worker -l info

# Terminal 3: (Opcional) Monitoreo de tareas con Flower
celery -A config flower --port=5555
```

!!! note "Importante"
    Asegúrate de que Redis esté corriendo antes de iniciar Celery. Sin Redis, las tareas asíncronas no se podrán encolar.

## Documentación de la API

- **Swagger UI:** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/redoc/`
- **OpenAPI Schema:** `http://localhost:8000/api/schema/`
