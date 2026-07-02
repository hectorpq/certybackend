# Dependencias

## Backend (Python)

Instalación: `pip install -r requirements.txt`

### Principales

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| Django | 5.2 | Framework web |
| djangorestframework | 3.14 | API REST |
| djangorestframework-simplejwt | — | JWT authentication |
| django-cors-headers | — | CORS |
| django-filter | — | Filtros para DRF |
| drf-spectacular | — | OpenAPI/Swagger |
| celery | — | Tareas asíncronas |
| redis | — | Cliente Redis |
| psycopg2-binary | — | Driver PostgreSQL |
| gunicorn | — | Servidor WSGI producción |
| reportlab | — | Generación de PDFs |
| qrcode | — | Generación de QR |
| Pillow | — | Procesamiento de imágenes |
| sendgrid | — | API de correo |
| openpyxl | — | Lectura de Excel |
| pandas | — | Procesamiento de datos |
| pytest | — | Testing |
| pytest-cov | — | Cobertura |

## Frontend (Node.js)

Instalación: `npm ci`

### Principales

| Paquete | Propósito |
|---------|-----------|
| react 18 | UI framework |
| react-router-dom 6 | Enrutamiento |
| @tanstack/react-query 5 | Estado del servidor |
| axios | Cliente HTTP |
| react-hook-form + zod | Formularios + validación |
| recharts | Gráficos |
| tailwindcss 3 | Estilos utilitarios |
| lucide-react | Iconos |
| vite 5 | Build tool |
| typescript 5 | Tipado estático |
| vitest | Testing unitario |
| @playwright/test 1.61 | Testing E2E |
| eslint + prettier | Linter + formateo |

## Requisitos del Sistema

| Herramienta | Versión Mínima |
|-------------|----------------|
| Python | 3.11+ |
| Node.js | 20 LTS |
| PostgreSQL | 15+ |
| Redis | 7+ |
| Docker | 24+ (opcional) |
