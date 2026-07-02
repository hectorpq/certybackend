# Estructura del Proyecto

## Monorepo

```
certisys/                  # Raíz del repositorio
├── certybackend/          # Backend Django
│   ├── api/               # API REST (views, serializers, permissions, audit)
│   ├── certificados/      # Certificado + Template models
│   ├── config/            # settings, celery, urls (root)
│   ├── core/              # Mixins, utilidades base
│   ├── deliveries/        # DeliveryLog model
│   ├── events/            # Event, Enrollment, Invitation models
│   ├── instructors/       # Instructor model
│   ├── participants/      # Participant model
│   ├── procesos/          # Bulk import services
│   ├── services/          # PDF, Email, WhatsApp services + Celery tasks
│   ├── users/             # Custom User model
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── Jenkinsfile
│   └── docs/              # Documentación MkDocs
│
├── certyfront/            # Frontend React
│   ├── src/
│   │   ├── components/    # layout/ + ui/ (atomic components)
│   │   ├── contexts/      # ThemeContext
│   │   ├── hooks/         # React Query hooks
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service layer (Axios)
│   │   ├── types/         # TypeScript interfaces
│   │   └── utils/         # errorHandling
│   ├── e2e/               # Playwright tests
│   ├── Dockerfile
│   └── Jenkinsfile
```

## Backend — Apps Django

| App | Modelos | Propósito |
|-----|---------|-----------|
| `api` | AuditLog | REST endpoints, permisos, serializers, auditoría |
| `certificados` | Certificate, Template | Certificados y plantillas visuales |
| `events` | Event, EventCategory, Enrollment, EventInvitation | Gestión de eventos e inscripciones |
| `participants` | Participant | Participantes/estudiantes |
| `users` | User (Custom) | Usuarios con roles |
| `instructors` | Instructor | Instructores con firma digital |
| `deliveries` | DeliveryLog | Registro de entregas |
| `services` | — | Lógica de negocio: PDF, Email, WhatsApp, Celery |
| `procesos` | — | Procesamiento de Excel, bulk |
| `core` | — | Mixins base (SoftDelete) |
| `config` | — | Configuración Django, Celery, URLs root |
