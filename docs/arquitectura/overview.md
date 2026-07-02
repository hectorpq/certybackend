# Visión General de la Arquitectura

## Estilo Arquitectónico

**Cliente-Servidor con API REST** y frontend SPA (Single Page Application). El backend expone una API RESTful consumida por el frontend React. La comunicación es síncrona para operaciones CRUD y asíncrona (Celery + Redis) para procesos pesados (generación de PDFs, envío masivo de correos).

## Diagrama de Contexto (C4 — Nivel 1)

```
[Usuario Admin/Coord] ──HTTP──> [SPA React (Vite)] ──HTTP──> [API Django REST]
                                                                    │
[Usuario Participante] ──HTTP──> [SPA React (Vite)]                [Base de Datos PostgreSQL]
                                                                    │
[Usuario Verificador] ──HTTP──> [API Django REST]                 [Redis (Celery Broker)]
     (verificación pública)                                          │
                                                               [Celery Workers]
                                                                    │
                                                          ┌──────────┼──────────┐
                                                     [SendGrid] [Meta WhatsApp] [QR / PDF]
```

## Principios Arquitectónicos

- **API First:** Toda la lógica de negocio reside en el backend; el frontend es solo una capa de presentación
- **Stateless:** La API no mantiene estado de sesión; usa JWT para autenticación
- **Procesamiento asíncrono:** Operaciones intensivas (PDF, email masivo) se delegan a Celery
- **Soft Delete:** Los registros no se eliminan físicamente; se marcan con `is_deleted`
- **Auditabilidad:** Las acciones críticas se registran en `AuditLog`

## Tecnologías Clave

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| Backend API | Django 5.2 + DRF | Madurez, ORM, ecosistema, DRF para REST |
| Frontend | React 18 + Vite + TS | Rendimiento, tipado estático, tooling moderno |
| Base de datos | PostgreSQL 15 | Confiabilidad, JSONB, índices avanzados |
| Cache/Broker | Redis 7 | Velocidad, soporte nativo de Celery |
| Task queue | Celery | Escalabilidad, reintentos, scheduling |
| PDF | ReportLab | Control pixel-perfect sobre el layout |
| Email | SendGrid API | Alta entregabilidad, templates |
| WhatsApp | Meta Cloud API | Canal directo al participante |
| Contenedores | Docker + Docker Compose | Entorno reproducible |
