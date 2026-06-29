# 🎓 SystemCertification — Backend

API REST en Django + DRF para gestionar eventos, participantes, inscripciones,
certificados en PDF e invitaciones por email, con entrega opcional por
**WhatsApp (Meta Cloud API)**, generación de PDF con **ReportLab** y
tareas asíncronas con **Celery + Redis**.

---

## 📋 Tabla de Contenidos

- [Stack](#-stack-tecnológico)
- [Características](#-características)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación Local](#-instalación-local)
- [Despliegue con Docker](#-despliegue-con-docker)
- [Variables de Entorno](#-variables-de-entorno)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Flujo de Invitaciones con Sesión](#-flujo-de-invitaciones-con-sesión)
- [Importación Masiva desde Excel](#-importación-masiva-desde-excel)
- [API Reference (resumen)](#-api-reference-resumen)
- [CI/CD y Calidad](#-cicd-y-calidad)
- [Troubleshooting](#-troubleshooting)

---

## 🔧 Stack Tecnológico

| Componente | Detalle |
|---|---|
| **Framework** | Django 5.2.12 |
| **API** | Django REST Framework 3.14 |
| **Auth** | `djangorestframework-simplejwt` 5.3 + sesión Django |
| **Base de Datos** | PostgreSQL 15 |
| **Cache / Cola** | Redis 7 + Celery 5 |
| **PDF** | ReportLab 4.0.7 |
| **Email** | SMTP genérico (Brevo por defecto) |
| **WhatsApp** | Meta WhatsApp Cloud API |
| **Excel** | pandas 2.1 + openpyxl 3.1 |
| **Soft delete + history** | django-simple-history 3.7 |
| **OpenAPI** | drf-spectacular |
| **Producción** | Gunicorn 4 workers × 2 threads |
| **Lint** | black 24, flake8 7, isort 5.13 |
| **Cobertura** | coverage + Cobertura XML → SonarCloud |

---

## ✨ Características

- **Eventos**: CRUD + invitaciones masivas por email (archivo o JSON).
- **Participantes** (antes *Estudiantes*): CRUD con soft delete y `created_by`.
- **Inscripciones** (Enrollment): asistencia, certificados asociados.
- **Certificados**: PDF con QR + código de verificación, estados
  `pending → generated → sent / failed`, reintento de entrega, historial.
- **Entrega multicanal**: Email, WhatsApp (Meta Cloud API), link directo.
- **Invitaciones con sesión Django**: el invitado llega por link → el backend
  guarda el token en sesión → al hacer login o registro se asocia
  automáticamente al evento (ver [Flujo de Invitaciones](#-flujo-de-invitaciones-con-sesión)).
- **Importación Excel** (`/api/participants/import/`): valida columnas
  requeridas (`first_name`, `email` con `@gmail.com`) y crea certificados
  en bloque.
- **Generación masiva de certificados** y envío de emails en background
  con Celery.

---

## 📦 Requisitos Previos

- Python **3.10+**
- PostgreSQL **15+**
- Redis **7+** (para Celery)
- (Opcional) Docker + Docker Compose

---

## 🚀 Instalación Local

```bash
git clone https://github.com/hectorpq/certybackend.git
cd SystemCertification

python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Crear .env (ver sección Variables de Entorno)
cp .env.example .env  # o crear manualmente

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Servidor en `http://localhost:8000`.

### Tests

```bash
# Suite completa con cobertura
pytest --cov=. --cov-report=xml:coverage.xml --cov-report=term

# Tests rápidos de invitación
pytest api/test_invitation_session_flow.py -v

# Tests unitarios
pytest api/test_unit.py -v
```

### Linters

```bash
black --line-length=120 .
flake8 --max-line-length=120 --extend-ignore=E203,W503 .
isort --profile black --line-length 120 .
```

---

## 🐳 Despliegue con Docker

`docker-compose.yml` levanta **db**, **redis**, **web** (Django + gunicorn),
**celery_worker**, **jenkins** y **sonarqube**.

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

- Web: `http://localhost:8000`
- Jenkins: `http://localhost:9080`
- SonarQube: `http://localhost:9001`

> **Nota de seguridad**: el servicio `web` NO monta `/var/run/docker.sock`.
> Solo `jenkins` lo necesita para CI/CD.

---

## ⚙️ Variables de Entorno

Crea un archivo `.env` en la raíz. Las mínimas son:

```env
# Django
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# DB
DB_NAME=certificados_db
DB_USER=certificados_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# Email (Brevo SMTP por defecto)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Frontend (para armar URLs de invitación)
FRONTEND_URL=https://app.certypro.app

# WhatsApp (Meta Cloud API)
META_WHATSAPP_TOKEN=EAAB...
META_WHATSAPP_PHONE_ID=1125933260596105

# Google OAuth (opcional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Las dependencias en `requirements.txt` están **pineadas con `==`** (incluyendo
`urllib3`, `sqlparse`, `zipp`, `requests`, `Pillow`) para builds reproducibles.

---

## 📁 Estructura del Proyecto

```
SystemCertification/
├── api/                       # Endpoints REST
│   ├── views.py              # ViewSets grandes (eventos, certificados, invitaciones)
│   ├── invitation_helpers.py # Lógica extraída de invitaciones
│   ├── serializers.py
│   ├── permissions.py
│   ├── test_invitation_session_flow.py  # 13 tests del flujo de sesión
│   ├── test_unit.py
│   └── test_views.py
├── certificados/             # Modelos Certificate, Template, DeliveryLog
├── events/                   # Event, Enrollment, EventInvitation
├── participants/             # Participant (con soft delete + history)
├── users/                    # Custom User (roles: admin, coordinator, participante)
├── instructors/              # Instructor
├── procesos/                 # Importación Excel
├── services/                 # pdf, email, whatsapp
├── core/                     # helpers, mixins
├── config/                   # settings, urls, wsgi/asgi
├── certificates/pdfs/        # PDFs generados (no versionado)
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/        # CI: lint, tests, security, sonar, deploy
```

---

## 🔄 Flujo de Invitaciones con Sesión

Diagrama simplificado:

```
1) Admin crea evento + invitación
   POST /api/events/{id}/invitations/send-invitations/
   emails = ["ana@gmail.com"]
   → crea EventInvitation(token=UUID, status=pending)
   → envía email con link /invitations/<token>/

2) Ana abre el link
   GET /api/invitations/<token>/
   → valida token + expiración
   → request.session["token_invitacion"] = str(token)
   → request.session["invitacion_email"] = "ana@gmail.com"
   → retorna { login_url, register_url, event_id, ... }

3) Ana hace login o registro
   POST /api/login/  (o /api/register/)
   → user.email == invitation.email (validación)
   → acepta la invitación: crea Participant + Enrollment + Certificate
   → invitation.status = "accepted"
   → limpia la sesión
   → retorna { access, refresh, redirect_url: "/events/<id>" }
```

**Validaciones clave** (ver `api/invitation_helpers.py`):

- El `user.email` debe coincidir con `invitation.email` (anti-privilege-escalation).
- La invitación no debe estar expirada ni ya respondida.
- La creación de `Participant` + `Enrollment` + `Certificate` ocurre dentro
  de `transaction.atomic()`.
- El `document_id` se genera con `uuid.uuid4().hex[:8]` para evitar
  colisiones con DNIs reales.

---

## 📊 Importación Masiva desde Excel

Endpoint: `POST /api/participants/import/`

**Columnas requeridas** (validadas en `procesos/services.py`):
- `first_name` (obligatorio)
- `email` con sufijo `@gmail.com` (obligatorio)
- `document_id` (obligatorio)
- `last_name`, `phone` (opcionales)

Si falta cualquier columna requerida, se retorna `400` con la lista de filas
con error y la importación **no se ejecuta parcialmente**.

Tras importar, el sistema crea automáticamente los certificados y los envía
por email (a través de Celery).

---

## 🔌 API Reference (resumen)

| Recurso | Endpoint base | Notas |
|---|---|---|
| Auth | `/api/auth/...` | JWT login/refresh + Google OAuth |
| Register | `/api/register/` | Auto-asocia invitación si hay token en sesión |
| Login | `/api/login/` | Auto-asocia invitación si hay token en sesión |
| Participantes | `/api/participants/` | CRUD + `import/` (Excel) |
| Eventos | `/api/events/` | CRUD + `invitations/send-invitations/`, `invitations/send-all/`, `stats/` |
| Invitaciones | `/api/invitations/<token>/` | GET (público) + `accept/`, `register/` |
| Certificados | `/api/certificates/` | CRUD + `generate/`, `deliver/`, `verify/`, `history/` |
| Entregas | `/api/deliveries/` | Historial de envíos |
| Templates | `/api/templates/` | Plantillas PDF |
| Instructores | `/api/instructors/` | CRUD |
| OpenAPI | `/api/schema/`, `/api/docs/` | drf-spectacular |

---

## ✅ CI/CD y Calidad

GitHub Actions ejecuta en cada PR y push:

1. **Lint**: `black --check`, `flake8`, `isort --check`.
2. **Tests**: `pytest` con cobertura → `coverage.xml` (formato Cobertura).
3. **Security SAST**: Bandit.
4. **Security SCA**: `pip-audit` sobre `requirements.txt`.
5. **Migrations check**: `manage.py makemigrations --check --dry-run`.
6. **Build check**: сборка Docker.
7. **SonarCloud**: análisis + Quality Gate (cobertura > 80% en código nuevo).

Configuración en `.github/workflows/` + `sonar-project.properties`.

---

## 🔍 Troubleshooting

- **`psycopg2` no compila**: instala `libpq-dev` y `gcc` (Linux) o usa la
  imagen Docker oficial.
- **`CSRF verification failed` en POST**: el cliente debe enviar la cookie
  `csrftoken` en el header `X-CSRFToken`. En DRF con `SessionAuthentication`
  la cookie se emite en el primer GET.
- **Tests flaky `test_changelog_restored_display`**: conocido, usar
  `pytest -k "not changelog_restored_display"`.
- **Email no llega**: revisar `EMAIL_USE_TLS`/`SSL` en `.env`; el backend
  ahora tolera valores truthy no estándar (`true`/`1`/`yes`).

---

**Última actualización**: 26 de junio de 2026  
**Versión**: 4.0 (Sesión Django + Excel + SonarCloud)
