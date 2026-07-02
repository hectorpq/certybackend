# Variables de Entorno

## Backend (`.env`)

| Variable | Requerida | Descripción | Ejemplo |
|----------|-----------|-------------|---------|
| `SECRET_KEY` | Sí | Clave secreta de Django | `django-insecure-...` |
| `DEBUG` | Sí | Modo debug | `True` / `False` |
| `ALLOWED_HOSTS` | Sí | Hosts permitidos (coma separados) | `localhost,api.certypro.com` |
| `DB_NAME` | Sí | Nombre de la base de datos | `certificados_db` |
| `DB_USER` | Sí | Usuario PostgreSQL | `postgres` |
| `DB_PASSWORD` | Sí | Contraseña PostgreSQL | `123456` |
| `DB_HOST` | Sí | Host PostgreSQL | `localhost` / `db` |
| `DB_PORT` | Sí | Puerto PostgreSQL | `5432` |
| `REDIS_URL` | Sí | URL de Redis (Celery broker) | `redis://localhost:6379/0` |
| `CORS_ALLOWED_ORIGINS` | Sí | Orígenes CORS | `http://localhost:5173` |
| `SENDGRID_API_KEY` | No | API key de SendGrid | `SG.xxxxx` |
| `WHATSAPP_TOKEN` | No | Token de Meta WhatsApp | `EAAT...` |
| `WHATSAPP_PHONE_ID` | No | ID de teléfono de WhatsApp | `123456789` |
| `GOOGLE_CLIENT_ID` | No | Client ID de Google OAuth | `xxxx.apps.googleusercontent.com` |
| `EMAIL_BACKEND` | No | Backend de correo | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | No | Servidor SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | No | Puerto SMTP | `587` |
| `EMAIL_USE_TLS` | No | TLS | `True` |
| `EMAIL_HOST_USER` | No | Usuario SMTP | `user@gmail.com` |
| `EMAIL_HOST_PASSWORD` | No | Contraseña SMTP | `xxxx` |
| `DEFAULT_FROM_EMAIL` | No | Remitente por defecto | `noreply@certypro.com` |

## Frontend (`.env.production`)

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `VITE_API_URL` | Sí | URL base del backend | `https://api.certypro.com` |
