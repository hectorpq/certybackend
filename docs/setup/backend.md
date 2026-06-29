# Instalación del Backend (Django API)

Esta guía detalla los pasos para instalar, configurar y ejecutar el backend del sistema CertySys.

## 🔧 Stack Tecnológico

| Componente      | Detalle                               |
| --------------- | ------------------------------------- |
| **Framework**   | Django 5.2.12                         |
| **API**         | Django REST Framework                 |
| **Base de Datos** | PostgreSQL 15+                        |
| **PDF**         | ReportLab                             |
| **Email**       | SendGrid                              |
| **WhatsApp**    | Meta Cloud API                        |
| **Auth**        | Custom User Model + Simple JWT        |
| **Tareas Asíncronas** | Celery + Redis                  |

---

## 📦 Requisitos Previos

- Python 3.10+
- PostgreSQL 15+ en ejecución
- Git
- Redis en ejecución (para Celery)

### Cuentas Externas
- **SendGrid**: Para envío de emails (API Key).
- **Meta (Facebook)**: Para la API de WhatsApp Cloud (Token y Phone ID).
- **Google Cloud**: Para autenticación con Google (Client ID).

---

## 🚀 Instalación

### 1. Clonar Repositorio
```bash
git clone https://github.com/Erick-Franco/CertySys.git
cd certysys/certybackend
```

### 2. Crear y Activar Entorno Virtual
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS/Linux (Bash)
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Base de Datos PostgreSQL
Crea la base de datos y el usuario según las instrucciones del `README.md` principal.

### 5. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz de `certybackend/` y configúralo con las credenciales de la base de datos, Django, Email (Gmail) y WhatsApp (Twilio).

```env
# certybackend/.env

DB_NAME=certificados_db
DB_USER=certificados_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=tu-secret-key-de-django
DEBUG=True

# ... resto de variables (EMAIL, TWILIO, etc.)
```

### 6. Aplicar Migraciones y Crear Superusuario
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Ejecutar Servidor
```bash
python manage.py runserver
```
El backend estará disponible en `http://localhost:8000`.