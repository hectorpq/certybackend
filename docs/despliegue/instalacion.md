# Instalación

## Requisitos Previos

- Python 3.11+
- Node.js 20 LTS
- PostgreSQL 15+
- Redis 7+

## Backend

```bash
git clone <repo-url>
cd certybackend

# Entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Colectar archivos estáticos
python manage.py collectstatic --noinput

# Iniciar servidor de desarrollo
python manage.py runserver
```

## Frontend

```bash
cd certyfront
npm ci
npm run dev
```

El servidor de desarrollo de Vite escucha en `http://localhost:5173`. Por defecto, proxy inverso a `http://localhost:8000`.

## Servicios Adicionales

```bash
# Worker Celery (para tareas asíncronas)
celery -A config worker -l info

# Redis (obligatorio para Celery)
redis-server
```

## Docker (Alternativa)

```bash
cd certybackend
docker-compose up -d
```

Esto inicia PostgreSQL, Redis, Django + Gunicorn, Celery Worker, Jenkins y SonarQube.
