# Diagrama de Componentes (C4 — Nivel 3)

## Propósito

Descomponer cada contenedor en sus componentes internos principales.

## API Django — Componentes Internos

```
api/
├── views.py          # ViewSets: Certificate, Event, Participant, Instructor, Template, Enrollment, DeliveryLog, AuditLog
│                     # APIViews: Login, Register, GoogleAuth, CurrentUser, Bulk*
├── serializers.py    # 25+ serializadores (Certificate*, Event*, Participant*, Template*, Enrollment*, etc.)
├── permissions.py    # 8 clases de permiso (IsAdmin, IsOperationalUser, CanManage*, etc.)
├── models.py         # AuditLog
├── urls.py           # Router (SimpleRouter) + rutas manuales
└── audit.py          # log_action(), get_client_ip()

certificados/
├── models.py         # Certificate, Template
├── admin.py

events/
├── models.py         # Event, EventCategory, Enrollment, EventInvitation
├── admin.py

participants/
├── models.py         # Participant (antes Student)
├── admin.py

users/
├── models.py         # User (Custom)
├── admin.py

instructors/
├── models.py         # Instructor

deliveries/
├── models.py         # DeliveryLog

services/
├── pdf_service.py    # PDFService (ReportLab + QR)
├── email_service.py  # EmailService (SendGrid)
├── whatsapp_service.py # WhatsAppService (Meta Cloud API)
├── tasks.py          # Tareas Celery

procesos/
├── services.py       # ExcelProcessingService, BulkCertificateGeneratorService

config/
├── settings.py       # Configuración Django
├── celery.py         # App Celery
├── urls.py           # URL root
├── wsgi.py / asgi.py

core/
├── mixins.py         # SoftDeleteMixin
```

## React SPA — Componentes Internos

```
src/
├── App.tsx                    # Router + QueryClientProvider + ThemeProvider
├── components/
│   ├── layout/                # Layout, Sidebar
│   └── ui/                    # Button, Modal, Card, Pagination, FileUpload, SignaturePad, etc.
├── contexts/                  # ThemeContext
├── hooks/                     # useAuth, useCertificates, useEvents, useInstructors, useStudents, useTemplates, useTheme
├── pages/
│   ├── auth/                  # Login, Register
│   ├── bulk/                  # BulkGeneratePage (4-step wizard)
│   ├── certificates/          # List + detail
│   ├── dashboard/             # Stats dashboard
│   ├── events/ + detail/      # List + detalle completo
│   ├── instructors/           # CRUD
│   ├── invitation/            # Página pública por token
│   ├── students/              # CRUD + import
│   └── templates/             # CRUD + canvas interactivo
├── services/                  # api.ts (Axios), authService, certificateService, eventService, participantService, instructorService
├── types/                     # Interfaces TypeScript
└── utils/                     # errorHandling.ts
```

## Flujo de una Solicitud Típica

```
Usuario → React (UI)
  → Hook (useQuery/useMutation)
    → Service (certificateService.ts)
      → api.ts (Axios: JWT interceptor)
        → HTTP GET /api/certificates/
          → urls.py → CertificateViewSet.list()
            → Permission check (CanManageCertificates)
              → Certificate.objects.filter(...)
                → Serializer (CertificateListSerializer)
                  → JSON Response
```

## Flujo de una Operación Asíncrona

```
Usuario → BulkGeneratePage (4-step wizard)
  → Confirma los datos
    → POST /api/certificates/generate-bulk/ (multipart)
      → BulkCertificateGenerationView
        → ExcelProcessingService.process()
          → Por cada fila:
              1. Crea/encuentra Participant
              2. Crea/encuentra Enrollment
              3. Crea Certificate (status=pending)
              4. Celery: generate_certificate_pdf_task.delay(cert_id)
              5. Celery: send_certificate_email_task.delay(cert_id, email)
                  → EmailService.send_certificate()
                    → SendGrid API
```
