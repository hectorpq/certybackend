# 🚀 Guía Rápida - Comandos Útiles

## ⚡ Inicio Rápido (5 minutos)

```bash
# 1. Activar entorno virtual
.venv\Scripts\Activate.ps1  # PowerShell Windows
source .venv/bin/activate    # Bash macOS/Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Migrar base de datos
python manage.py migrate

# 4. Crear admin
python manage.py createsuperuser

# 5. Ejecutar servidor
python manage.py runserver

# 6. Acceder
http://localhost:8000/admin
```

---

## 🎮 Comandos Django Comunes

### Migraciones
```bash
# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Ver estado de migraciones
python manage.py showmigrations

# Ver SQL de una migración
python manage.py sqlmigrate app_name 0001
```

### Base de Datos
```bash
# Crear copia de seguridad
python manage.py dumpdata > backup.json

# Restaurar base de datos
python manage.py loaddata backup.json

# Limpiar base de datos (CUIDADO!)
python manage.py flush
```

### Shell Interactivo
```bash
# Acceder a Django shell
python manage.py shell

# Dentro del shell:
from certificados.models import Certificate
from students.models import Student

# Crear estudiante
s = Student.objects.create(
    document_id="123456",
    first_name="Juan",
    last_name="Pérez",
    email="juan@example.com",
    phone="+57123456789"
)

# Ver estudiantes
Student.objects.all()

# Filtrar
Certificate.objects.filter(status='pending')

# Salir
exit()
```

### Usuarios
```bash
# Crear superusuario
python manage.py createsuperuser

# Cambiar contraseña
python manage.py changepassword username

# Crear usuario staff
python manage.py shell
> python from django.contrib.auth import get_user_model
> User = get_user_model()
> user = User.objects.create_user('username', 'email@example.com', 'password')
> user.is_staff = True
> user.save()
```

---

## 📊 Scripts de Utilidad

### Script: Generar Certificados en Batch
```bash
# Crear archivo: scripts/generate_batch.py

from certificados.models import Certificate
from events.models import Event

# Obtener evento y sus estudiantes
event = Event.objects.get(id=1)

# Iterar estudiantes
for enrollment in event.enrollment_set.all():
    if enrollment.attendance:
        cert = Certificate.objects.create(
            student=enrollment.student,
            event=event
        )
        cert.generate()
        print(f"✅ {enrollment.student.full_name}")

# Ejecutar:
python manage.py shell < scripts/generate_batch.py
```

### Script: Importar Estudiantes desde CSV
```bash
# Crear archivo: scripts/import_students.py

import csv
from students.models import Student

with open('students.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        Student.objects.get_or_create(
            document_id=row['documento'],
            defaults={
                'first_name': row['nombre'],
                'last_name': row['apellido'],
                'email': row['email'],
                'phone': row['telefono']
            }
        )
        print(f"✅ {row['nombre']}")

# Estructura CSV esperada:
# documento,nombre,apellido,email,telefono
# 123456,Juan,Pérez,juan@example.com,+57123456789
# 789012,María,García,maria@example.com,+57987654321

# Ejecutar:
python manage.py shell < scripts/import_students.py
```

---

## 🧪 Testing

### Ejecutar tests
```bash
# Todos los tests
python manage.py test

# Tests de una app específica
python manage.py test certificados

# Tests de una clase específica
python manage.py test certificados.tests.CertificateTestCase

# Tests con verbose
python manage.py test -v 2

# Tests con pattern
python manage.py test certificados.tests -k "test_generate"
```

### Ejemplo de test
```python
# certificados/tests.py

from django.test import TestCase
from certificados.models import Certificate
from students.models import Student
from events.models import Event

class CertificateTestCase(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            document_id="123456",
            first_name="Test",
            last_name="Student",
            email="test@example.com"
        )
        self.event = Event.objects.create(
            name="Test Event",
            event_date="2025-03-10"
        )
    
    def test_certificate_generation(self):
        cert = Certificate.objects.create(
            student=self.student,
            event=self.event
        )
        cert.generate()
        self.assertEqual(cert.status, 'generated')
        self.assertIsNotNone(cert.pdf_url)
```

---

## 🐛 Debugging

### Django Debug Toolbar
```bash
# Instalar
pip install django-debug-toolbar

# settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

# Acceso: http://localhost:8000/ → Toolbar lateral derecha
```

### Logs
```python
# Habilitar logs
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# En código
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

---

## 📦 Limpeza y Mantenimiento

### Limpiar archivos temporales
```bash
# Limpiar cache de Python
find . -type d -name __pycache__ -exec rm -r {} +

# Limpiar compilados
find . -type f -name "*.pyc" -delete

# En PowerShell
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
```

### Recolectar archivos estáticos (Producción)
```bash
python manage.py collectstatic --noinput
```

### Optimizar BD (PostgreSQL)
```sql
-- Conectarse con psql
psql -U certificados_user -d certificados_db

-- Analizar tabla
ANALYZE certificados_certificate;

-- Ver índices
\d certificados_certificate
```

---

## 🚀 Despliegue a Producción

### Preparar para producción

```bash
# 1. Instalar Gunicorn
pip install gunicorn

# 2. Crear archivo de servicio (systemd)
# /etc/systemd/system/certificados.service

[Unit]
Description=Certificados Django App
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/certificados
Environment="PATH=/var/www/certificados/.venv/bin"
ExecStart=/var/www/certificados/.venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target

# 3. Iniciar servicio
sudo systemctl start certificados
sudo systemctl enable certificados
sudo systemctl status certificados

# 4. Configurar Nginx (reverse proxy)
# /etc/nginx/sites-available/certificados

server {
    listen 80;
    server_name tudominio.com;

    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/certificados/static/;
    }

    location /media/ {
        alias /var/www/certificados/media/;
    }
}

# 5. Habilitar sitio
sudo ln -s /etc/nginx/sites-available/certificados /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📱 API Testing con Postman

### Colección recomendada

```json
{
  "info": {
    "name": "Certificados API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Get Token",
          "request": {
            "method": "POST",
            "url": "http://localhost:8000/api-token-auth/",
            "body": {
              "username": "admin",
              "password": "password"
            }
          }
        }
      ]
    },
    {
      "name": "Certificates",
      "item": [
        {
          "name": "List All",
          "request": {
            "method": "GET",
            "url": "http://localhost:8000/api/certificates/"
          }
        },
        {
          "name": "Generate",
          "request": {
            "method": "POST",
            "url": "http://localhost:8000/api/certificates/1/generate/"
          }
        },
        {
          "name": "Deliver",
          "request": {
            "method": "POST",
            "url": "http://localhost:8000/api/certificates/1/deliver/",
            "body": {
              "method": "email",
              "recipient": "student@example.com"
            }
          }
        }
      ]
    }
  ]
}
```

---

## 🔗 Enlaces Útiles

- [Django Management Commands](https://docs.djangoproject.com/en/5.2/ref/django-admin/)
- [DRF Testing](https://www.django-rest-framework.org/api-guide/testing/)
- [PostgreSQL CLI](https://www.postgresql.org/docs/current/app-psql.html)
- [Gunicorn Settings](https://docs.gunicorn.org/)

---

**Última actualización**: 29 de marzo de 2026
