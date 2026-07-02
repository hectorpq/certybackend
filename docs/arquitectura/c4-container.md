# Diagrama de Contenedores (C4 — Nivel 2)

## Propósito

Descomponer el sistema en contenedores (aplicaciones, almacenes de datos, colas) y mostrar las relaciones entre ellos.

## Contenedores

```
┌─────────────────────────────────────────────────────────┐
│                    Certy System                          │
│                                                         │
│  ┌──────────────────┐      ┌────────────────────────┐   │
│  │   React SPA       │      │   Django REST API      │   │
│  │   (Vite + TS)     │──────│   (DRF + Gunicorn)     │   │
│  │   Puerto 5173     │HTTP  │   Puerto 8000           │   │
│  └──────────────────┘      └───────────┬────────────┘   │
│                                        │                 │
│  ┌──────────────────┐      ┌───────────▼────────────┐   │
│  │   PostgreSQL 15   │◄─────│   Celery Workers       │   │
│  │   Puerto 5432     │ SQL  │   (tasks.py)           │   │
│  └──────────────────┘      └───────────┬────────────┘   │
│                                        │                 │
│                               ┌────────▼────────┐       │
│                               │   Redis 7        │       │
│                               │   Puerto 6379    │       │
│                               └─────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## Detalle de Contenedores

### React SPA

- **Tecnología:** React 18 + Vite 5 + TypeScript 5 + TailwindCSS 3
- **Responsabilidad:** Interfaz de usuario, enrutamiento, estado del servidor (TanStack Query)
- **Comunicación:** HTTP/HTTPS → API Django (proxy Vite en desarrollo, Nginx en producción)
- **Autenticación:** JWT almacenado en localStorage, refresco automático vía Axios interceptor

### Django REST API

- **Tecnología:** Django 5.2 + DRF 3.14 + Gunicorn
- **Responsabilidad:** Lógica de negocio, ORM, autenticación, autorización, validación
- **Endpoints:** ~40 endpoints REST organizados en ViewSets
- **Workers:** Gunicorn con 2-4 workers

### PostgreSQL

- **Responsabilidad:** Almacenamiento persistente de todos los datos del dominio
- **Esquemas:** certificados, events, participants, users, instructors, deliveries, api (AuditLog)
- **Índices:** Los campos más consultados (status, action, user, certificate) tienen índices explícitos

### Redis

- **Responsabilidad:** Broker de mensajería para Celery (cola de tareas y backend de resultados)
- **Uso:** Almacenamiento de resultados de tareas asíncronas

### Celery Workers

- **Responsabilidad:** Ejecución asíncrona de tareas pesadas (generación de PDFs, envío de correos)
- **Tareas:** `send_certificate_email_task`, `generate_certificate_pdf_task`, `send_bulk_certificates_task`
- **Reintentos:** Configurados con backoff exponencial (max_retries=2-3)
