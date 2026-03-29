# 🎓 Sistema de Certificación - Gestión Académica Integral

Sistema completo de gestión y distribución de certificados académicos digitales con soporte para múltiples canales de entrega (Email, WhatsApp, Enlaces directos).

## 📋 Tabla de Contenidos
- [Stack Tecnológico](#stack-tecnológico)
- [Características](#características)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [API Reference](#api-reference)
- [Modelos de Datos](#modelos-de-datos)
- [Uso del Admin](#uso-del-admin)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Stack Tecnológico

| Componente | Detalle |
|-----------|---------|
| **Framework** | Django 5.2.12 |
| **API** | Django REST Framework |
| **Base de Datos** | PostgreSQL 15+ |
| **PDF** | ReportLab 4.0.7 |
| **Email** | Gmail SMTP + Django Email |
| **WhatsApp** | Twilio 8.10.0 |
| **Auth** | Django Auth + Custom User Model |
| **Env** | Django-Environ 0.10.0 |

---

## ✨ Características

### 🎯 Gestión de Certificados
- ✅ Generación automática de PDFs con ReportLab
- ✅ Códigos de verificación únicos (MD5)
- ✅ Estados de ciclo de vida: Pending → Generated → Sent/Failed
- ✅ Vencimiento automático de certificados
- ✅ Validación de asistencia del estudiante

### 📤 Canales de Entrega
- 📧 **Email**: Envío vía Gmail SMTP
- 💬 **WhatsApp**: Integración con Twilio
- 🔗 **Link**: Acceso directo (sin envío)
- 📊 **Registro**: Cada entrega registrada en `DeliveryLog`

### 👨‍💼 Admin & Permisos
- Acciones masivas en el admin
- Control granular de permisos
- Reintentos de entrega
- Historial de envíos

### 🔒 Seguridad
- Autenticación JWT-ready
- Permisos por usuario/staff
- Verificación de asistencia
- Timestamps de auditoría

---

## 📦 Requisitos Previos

```bash
# Verificar Python 3.10+
python --version

# PostgreSQL 15+ en ejecución
# psql --version

# Git
git --version
```

### Cuentas Externas Requeridas
- **Gmail**: Para envío de emails (credenciales SMTP)
- **Twilio**: Para WhatsApp (Account SID, Auth Token, número de teléfono)

---

## 🚀 Instalación

### 1. Clonar Repositorio
```bash
git clone https://github.com/Erick-Franco/SystemCertification.git
cd SystemCertification
```

### 2. Crear Virtual Environment
```bash
# PowerShell (Windows)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Bash (macOS/Linux)
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependencias principales**:
```
Django==5.2.12
djangorestframework==3.14.0
psycopg2-binary==2.9.9
reportlab==4.0.7
twilio==8.10.0
django-environ==0.10.0
python-decouple==3.8
```

### 4. Crear Base de Datos PostgreSQL
```sql
CREATE DATABASE certificados_db;
CREATE USER certificados_user WITH PASSWORD 'secure_password';
ALTER ROLE certificados_user SET client_encoding TO 'utf8';
ALTER ROLE certificados_user SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE certificados_db TO certificados_user;
```

### 5. Aplicar Migraciones
```bash
python manage.py migrate
```

### 6. Crear Superusuario
```bash
python manage.py createsuperuser
# Ingresa: username, email, password (x2)
```

### 7. Ejecutar Servidor de Desarrollo
```bash
python manage.py runserver
# Accede a: http://localhost:8000/admin
```

---

## ⚙️ Configuración

### 1. Archivo `.env` (Raíz del Proyecto)

```env
# ========== BASE DE DATOS ==========
DB_NAME=certificados_db
DB_USER=certificados_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# ========== DJANGO ==========
SECRET_KEY=your-django-secret-key-here
DEBUG=True  # False en producción

# ========== EMAIL (Gmail SMTP) ==========
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # NO tu contraseña normal
DEFAULT_FROM_EMAIL=your-gmail@gmail.com

# ========== WhatsApp (Twilio) ==========
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxX
TWILIO_PHONE_NUMBER=+1234567890

# ========== CERTIFICADOS ==========
CERTIFICATE_EXPIRY_DAYS=365
CERTIFICATE_VERIFICATION_ENABLED=True
```

### 2. Configurar Gmail para SMTP

1. **Habilitar 2FA** en tu cuenta Google
2. **Generar App Password**:
   ```
   Google Account → Security → App passwords → Select app=Mail, device=Windows
   ```
3. **Copiar contraseña** generada → Pegar en `EMAIL_HOST_PASSWORD` del `.env`

### 3. Configurar Twilio

1. **Crear cuenta** en [twilio.com](https://www.twilio.com)
2. **Obtener credenciales**:
   - Account SID
   - Auth Token
   - Virtual phone number (+1234567890)
3. **Pegar en `.env`**

### 4. Cargar Variables de Entorno
```bash
# Django carga automáticamente desde .env con django-environ
# No requiere comando especial
```

---

## 📁 Estructura del Proyecto

```
certificados_project/
│
├── config/                    # Configuración principal Django
│   ├── settings.py           # Configuración de apps, BD, etc
│   ├── urls.py               # Rutas principales
│   ├── asgi.py               # ASGI (producción)
│   └── wsgi.py               # WSGI (producción)
│
├── api/                       # REST API
│   ├── views.py              # ViewSets (CertificateViewSet, DeliveryLogViewSet)
│   ├── serializers.py        # Serializadores
│   ├── urls.py               # Rutas API
│   └── permissions.py        # Permisos personalizados
│
├── certificados/             # App principal - Gestión de certificados
│   ├── models.py             # Certificate, Template
│   ├── admin.py              # Admin actions (generate, deliver, etc)
│   ├── views.py              # Vistas
│   ├── serializers.py        # Serializadores
│   └── migrations/           # Migraciones de BD
│
├── services/                 # Servicios externos
│   ├── email_service.py      # EmailService (Gmail SMTP)
│   ├── pdf_service.py        # PDFService (ReportLab)
│   └── whatsapp_service.py   # WhatsAppService (Twilio)
│
├── students/                 # Gestión de estudiantes
│   ├── models.py             # Student model
│   ├── admin.py              # Admin
│   └── migrations/
│
├── events/                   # Gestión de eventos/cursos
│   ├── models.py             # Event, Enrollment
│   ├── admin.py              # Admin
│   └── migrations/
│
├── deliveries/               # Registro de entregas
│   ├── models.py             # DeliveryLog
│   ├── admin.py              # Admin
│   └── migrations/
│
├── users/                    # Auth custom
│   ├── models.py             # Custom User
│   ├── admin.py              # Admin
│   └── migrations/
│
├── core/                     # Utilidades comunes
│   ├── models.py             # Modelos compartidos
│   ├── helpers.py            # Funciones auxiliares
│   └── migrations/
│
├── instructors/              # Gestión de instructores
│   ├── models.py             # Instructor model
│   ├── admin.py              # Admin
│   └── migrations/
│
├── procesos/                 # Procesos y reportes
│   ├── admin.py              # Admin
│   └── migrations/
│
├── emails/                   # Notificaciones por email
│   ├── models.py             # Email templates, queues
│   ├── admin.py              # Admin
│   └── migrations/
│
├── scripts/                  # Scripts de utilidad
│   ├── example_real_delivery.py
│   └── regenerate_certs.py
│
├── certificates/             # Almacenamiento de archivos
│   └── pdfs/                # PDFs generados
│
├── manage.py                # CLI de Django
├── .env                     # Variables de entorno
├── .gitignore               # Gitignore
├── requirements.txt         # Dependencias Python
└── README.md               # Este archivo

```

---

## 🔌 API Reference

### Base URL
```
http://localhost:8000/api/
```

### Autenticación
- **Tipo**: Token/Session (REST Framework)
- **Headers requeridos**:
  ```
  Authorization: Bearer <token>
  Content-Type: application/json
  ```

---

### 📜 Endpoints: Certificados

#### 1. **Listar Certificados**
```
GET /api/certificates/
```

**Parámetros Query**:
```
?page=1
?search=student_name
?status=pending,generated,sent
```

**Respuesta** (200 OK):
```json
{
  "count": 50,
  "next": "http://.../api/certificates/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "student": {
        "id": 1,
        "full_name": "Juan Pérez",
        "email": "juan@example.com",
        "phone": "+57 123456789"
      },
      "event": {
        "id": 1,
        "name": "Python Avanzado",
        "event_date": "2025-03-15",
        "category": "Programming"
      },
      "status": "generated",
      "verification_code": "A1B2C3D4E5F6G7H8",
      "pdf_url": "/certificates/pdfs/cert_1.pdf",
      "issued_at": "2025-03-10T10:30:00Z",
      "expires_at": "2026-03-10T10:30:00Z"
    }
  ]
}
```

---

#### 2. **Crear Certificado**
```
POST /api/certificates/
```

**Body** (JSON):
```json
{
  "student_id": 1,
  "event_id": 1,
  "template_id": 1
}
```

**Respuesta** (201 Created):
```json
{
  "id": 1,
  "student": 1,
  "event": 1,
  "status": "pending",
  "verification_code": "A1B2C3D4E5F6G7H8",
  "pdf_url": "",
  "issued_at": "2025-03-10T10:30:00Z"
}
```

---

#### 3. **Obtener Detalles de Certificado**
```
GET /api/certificates/{id}/
```

**Respuesta** (200 OK):
```json
{
  "id": 1,
  "student": { ... },
  "event": { ... },
  "template": { ... },
  "status": "generated",
  "verification_code": "A1B2C3D4E5F6G7H8",
  "pdf_url": "/certificates/pdfs/cert_1.pdf",
  "expires_at": "2026-03-10",
  "issued_at": "2025-03-10T10:30:00Z",
  "updated_at": "2025-03-10T10:35:00Z",
  "deliveries": [
    {
      "id": 1,
      "delivery_method": "email",
      "status": "success",
      "recipient": "juan@example.com",
      "sent_at": "2025-03-10T10:35:00Z"
    }
  ]
}
```

---

#### 4. **Generar PDF de Certificado**
```
POST /api/certificates/{id}/generate/
```

**Body** (JSON):
```json
{
  "template_id": 1,
  "expires_in_days": 365
}
```

**Respuesta** (200 OK):
```json
{
  "success": true,
  "message": "Certificate generated successfully",
  "pdf_url": "/certificates/pdfs/cert_1.pdf",
  "verification_code": "A1B2C3D4E5F6G7H8"
}
```

**Errores**:
- `400 Bad Request`: Estudiante no asistió al evento
- `409 Conflict`: Certificado ya fue generado
- `500 Server Error`: Error al generar PDF

---

#### 5. **Entregar Certificado**
```
POST /api/certificates/{id}/deliver/
```

**Body** (JSON):
```json
{
  "method": "email",
  "recipient": "juan@example.com"
}
```

**Opciones de `method`**:
- `"email"` - Envía por Gmail SMTP
- `"whatsapp"` - Envía por Twilio WhatsApp
- `"link"` - Solo marca como entregado

**Respuesta** (200 OK):
```json
{
  "success": true,
  "message": "Certificate delivered successfully via email",
  "delivery_log_id": 1,
  "status": "success",
  "method": "email"
}
```

**Errores**:
- `400 Bad Request`: Certificado no generado aún
- `503 Service Unavailable`: Error de email/Twilio
- `401 Unauthorized`: Usuario no tiene permisos

---

#### 6. **Verificar Certificado (Público)**
```
GET /api/certificates/verify/{verification_code}/
```

**Parámetros**:
- `{verification_code}`: Código único del certificado (ej: A1B2C3D4E5F6G7H8)

**Respuesta** (200 OK):
```json
{
  "valid": true,
  "student": "Juan Pérez",
  "event": "Python Avanzado",
  "issued_date": "2025-03-10",
  "expiration_date": "2026-03-10",
  "verification_code": "A1B2C3D4E5F6G7H8"
}
```

**Errores**:
- `404 Not Found`: Código no existe
- `410 Gone`: Certificado expirado

---

#### 7. **Historial de Entregas**
```
GET /api/certificates/{id}/history/
```

**Respuesta** (200 OK):
```json
{
  "certificate_id": 1,
  "total_deliveries": 3,
  "deliveries": [
    {
      "id": 1,
      "method": "email",
      "status": "success",
      "recipient": "juan@example.com",
      "sent_at": "2025-03-10T10:35:00Z",
      "error_message": ""
    },
    {
      "id": 2,
      "method": "whatsapp",
      "status": "success",
      "recipient": "57 123456789",
      "sent_at": "2025-03-10T10:36:00Z"
    },
    {
      "id": 3,
      "method": "email",
      "status": "error",
      "recipient": "error@example.com",
      "error_message": "Invalid email address",
      "sent_at": "2025-03-10T10:37:00Z"
    }
  ]
}
```

---

### 📦 Endpoints: Entregas (DeliveryLog)

#### 1. **Listar Entregas**
```
GET /api/deliveries/
```

**Filtros Query**:
```
?status=success,error,pending
?method=email,whatsapp,link
?certificate=1
```

**Respuesta** (200 OK):
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "certificate": 1,
      "delivery_method": "email",
      "recipient": "juan@example.com",
      "status": "success",
      "sent_at": "2025-03-10T10:35:00Z",
      "is_successful": true
    }
  ]
}
```

---

#### 2. **Obtener Entrega Específica**
```
GET /api/deliveries/{id}/
```

**Respuesta** (200 OK):
```json
{
  "id": 1,
  "certificate": 1,
  "sent_by": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  },
  "delivery_method": "email",
  "recipient": "juan@example.com",
  "status": "success",
  "error_message": "",
  "sent_at": "2025-03-10T10:35:00Z",
  "updated_at": "2025-03-10T10:35:01Z",
  "is_successful": true,
  "is_failed": false,
  "is_pending": false
}
```

---

## 💾 Modelos de Datos

### Certificate
```python
class Certificate(models.Model):
    id              : BigInteger (PK)
    student_id      : ForeignKey(Student)
    event_id        : ForeignKey(Event)
    template_id     : ForeignKey(Template, nullable)
    generated_by_id : ForeignKey(User, nullable)
    verification_code : Unique CharField(50)
    pdf_url         : TextField (ruta local)
    status          : CharField choices=[pending, generated, sent, failed]
    expires_at      : DateTime
    issued_at       : DateTime (auto_now_add)
    updated_at      : DateTime (auto_now)
    
    # Métodos
    is_expired()    : bool
    generate()      : void (genera PDF)
    deliver(method) : DeliveryLog (email/whatsapp/link)
```

### DeliveryLog
```python
class DeliveryLog(models.Model):
    id                : BigInteger (PK)
    certificate_id    : ForeignKey(Certificate)
    sent_by_id        : ForeignKey(User, nullable)
    delivery_method   : CharField choices=[email, whatsapp, link]
    recipient         : CharField(200)
    status            : CharField choices=[success, error, pending]
    error_message     : TextField
    sent_at           : DateTime (auto_now_add)
    updated_at        : DateTime (auto_now)
    
    # Propiedades
    is_successful     : bool @property
```

### Student
```python
class Student(models.Model):
    id          : BigInteger (PK)
    document_id : Unique CharField(20)
    first_name  : CharField(100)
    last_name   : CharField(100)
    email       : Unique EmailField
    phone       : CharField(20, optional)
    is_active   : Boolean (default=True)
    created_at  : DateTime
    updated_at  : DateTime
    
    # Propiedades
    full_name   : str @property
```

### Event
```python
class Event(models.Model):
    id          : BigInteger (PK)
    name        : CharField(200)
    category    : CharField(100)
    event_date  : DateTime
    location    : CharField(200, optional)
    description : TextField(optional)
    instructor_id : ForeignKey(Instructor, nullable)
    is_active   : Boolean (default=True)
    created_at  : DateTime
    updated_at  : DateTime
```

### Template
```python
class Template(models.Model):
    id            : BigInteger (PK)
    created_by_id : ForeignKey(User, nullable)
    name          : CharField(100)
    category      : CharField(100)
    background_url : TextField
    preview_url   : TextField
    layout_config : JSONField
    is_active     : Boolean (default=True)
    created_at    : DateTime
    updated_at    : DateTime
```

---

## 👨‍💼 Uso del Admin

Accede a: **http://localhost:8000/admin**

### 1. Gestión de Certificados

#### Crear Certificado Nuevo
1. Ir a `Certificados` → `Certificados`
2. Click `+ Añadir Certificado`
3. Seleccionar:
   - **Estudiante**
   - **Evento**
   - **Template** (opcional)
4. Click `Guardar`

#### Generar PDF
1. Seleccionar certificados (checkboxes)
2. Dropdown `Acción` → `🎨 Generar Certificados`
3. Click `Ir`
4. Esperar a que se genere el PDF

#### Entregar vía Email
1. Seleccionar certificados
2. Dropdown → `📧 Entregar vía Email (REAL)`
3. Click `Ir`
4. Se envía automáticamente a correo del estudiante

#### Entregar vía WhatsApp
1. Seleccionar certificados
2. Dropdown → `💬 Entregar vía WhatsApp (REAL)`
3. Click `Ir`
4. Se envía automáticamente al número del estudiante

### 2. Ver Historial de Entregas
```
Admin → Entregas → DeliveryLog
```
Filtra por:
- **Estado**: success, error, pending
- **Método**: email, whatsapp, link
- **Certificado**: Seleccionar certificado

### 3. Gestionar Estudiantes
```
Admin → Estudiantes → Estudiantes
```
- Crear/editar estudiantes
- Ver certificados asociados
- Activar/desactivar

### 4. Gestionar Eventos
```
Admin → Eventos → Eventos
```
- Crear eventos
- Asignar instructor
- Ver estudiantes matriculados

---

## 💡 Ejemplos de Uso

### Ejemplo 1: API - Generar y Entregar Certificado

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"
HEADERS = {
    "Authorization": "Bearer your-token-here",
    "Content-Type": "application/json"
}

# 1. Crear certificado
create_data = {
    "student_id": 1,
    "event_id": 1,
    "template_id": 1
}
response = requests.post(
    f"{BASE_URL}/certificates/",
    json=create_data,
    headers=HEADERS
)
cert_id = response.json()["id"]
print(f"✅ Certificado creado: {cert_id}")

# 2. Generar PDF
generate_data = {
    "template_id": 1,
    "expires_in_days": 365
}
response = requests.post(
    f"{BASE_URL}/certificates/{cert_id}/generate/",
    json=generate_data,
    headers=HEADERS
)
print(f"✅ PDF generado: {response.json()['pdf_url']}")

# 3. Entregar por Email
deliver_data = {
    "method": "email",
    "recipient": "juan@example.com"
}
response = requests.post(
    f"{BASE_URL}/certificates/{cert_id}/deliver/",
    json=deliver_data,
    headers=HEADERS
)
print(f"✅ Certificado enviado: {response.json()['message']}")

# 4. Verificar entrega
response = requests.get(
    f"{BASE_URL}/certificates/{cert_id}/history/",
    headers=HEADERS
)
print(f"📊 Historial: {json.dumps(response.json(), indent=2)}")
```

### Ejemplo 2: Script Django - Entregar Batch

```python
# Ejecutar: python manage.py shell

from certificados.models import Certificate
from services.email_service import EmailService

# Obtener certificados pendientes
certs = Certificate.objects.filter(status='pending')[:10]

for cert in certs:
    # Generar PDF
    cert.generate()
    print(f"✅ {cert.student.full_name} - PDF generado")
    
    # Entregar por email
    result = cert.deliver(method='email')
    print(f"📧 {cert.student.email} - {result['status']}")
```

### Ejemplo 3: cURL - Verificar Certificado

```bash
# Verificar certificado (PÚBLICO - sin auth)
curl -X GET "http://localhost:8000/api/certificates/verify/A1B2C3D4E5F6G7H8/" \
  -H "Content-Type: application/json"

# Respuesta:
# {
#   "valid": true,
#   "student": "Juan Pérez",
#   "event": "Python Avanzado",
#   "issued_date": "2025-03-10",
#   "expiration_date": "2026-03-10"
# }
```

### Ejemplo 4: cURL - Listar Certificados

```bash
# Listar certificados generados
curl -X GET "http://localhost:8000/api/certificates/?status=generated" \
  -H "Authorization: Bearer your-token-here"
```

---

## 🔍 Troubleshooting

### ❌ Error: "No module named 'django'"
```bash
# Solución: Verificar venv activado
.venv\Scripts\Activate.ps1  # PowerShell Windows
source .venv/bin/activate    # Bash macOS/Linux

# Reinstalar dependencias
pip install -r requirements.txt
```

### ❌ Error: "FATAL: Ident authentication failed for user"
```bash
# Solución: Verificar credenciales de BD en .env
DB_USER=certificados_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
```

### ❌ Error: "Email not configured" o "SMTP Connection Error"
```bash
# Solución: Verificar configuración Gmail
1. ¿Habilité 2FA? Sí → Continuar
2. ¿Generé App Password? Sí
3. ¿Copié en EMAIL_HOST_PASSWORD? Sí
4. ¿Reinicié servidor? 
   python manage.py runserver
```

### ❌ Error: "Twilio Auth Error"
```bash
# Solución: Verificar credenciales Twilio
1. Accede a https://console.twilio.com
2. Copia Account SID → TWILIO_ACCOUNT_SID
3. Copia Auth Token → TWILIO_AUTH_TOKEN
4. Copia Phone Number → TWILIO_PHONE_NUMBER

# Verifica en .env (sin espacios)
TWILIO_ACCOUNT_SID=ACxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxx
TWILIO_PHONE_NUMBER=+1234567890
```

### ❌ Error: "Certificate PDF not found"
```bash
# Solución: Verificar directorio de PDFs
1. Crear directorio si no existe:
   mkdir certificates/pdfs
   
2. Verificar permisos de escritura:
   # PowerShell
   New-Item -ItemType Directory -Path "certificates/pdfs" -Force
```

### ❌ Error 403 Forbidden en API
```bash
# Solución: Problema de autenticación/permisos
1. ¿Incluiste Authorization header?
   Authorization: Bearer <token>
   
2. ¿El usuario es staff?
   Admin → Users → Editar usuario → ✓ Staff status

3. ¿Token válido?
   Panel admin → Tokens → Verificar token activo
```

### ❌ Error: "Student not found"
```bash
# Solución: Crear estudiante primero
1. Admin → Estudiantes → + Añadir Estudiante
2. Completar: nombre, documento, email, teléfono
3. Click Guardar
```

---

## 📚 Recursos Adicionales

- **Django Docs**: https://docs.djangoproject.com/en/5.2/
- **DRF Docs**: https://www.django-rest-framework.org/
- **ReportLab**: https://www.reportlab.com/docs/reportlab-userguide.pdf
- **Twilio**: https://www.twilio.com/docs
- **Gmail SMTP**: https://support.google.com/mail/answer/185833

---

## 👥 Contribuyentes

- **Erick Franco** - Desarrollo principal

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.

---

## ❓ Preguntas / Soporte

Para reportar bugs o sugerir mejoras:
1. Abre un issue en GitHub
2. Describe el problema detalladamente
3. Incluye logs y pasos para reproducir

---

**Última actualización**: 29 de marzo de 2026  
**Versión**: 3.0 (Entregas Reales Implementadas)
