# Changelog

## v1.0.0 (Fecha de lanzamiento)

### Features

- Gestión de eventos (CRUD + estados)
- Gestión de participantes (CRUD + importación Excel)
- Gestión de instructores con firma digital
- Gestión de plantillas visuales con canvas interactivo
- Generación de PDFs personalizados con QR y firma
- Envío de certificados por email (SendGrid) y WhatsApp (Meta Cloud API)
- Verificación pública de certificados mediante código único
- Carga masiva por Excel (4-step wizard)
- Autenticación JWT + Google OAuth
- Roles: admin, coordinador, participante
- Dashboard con estadísticas
- Soft delete en modelos principales
- Auditoría de acciones críticas (AuditLog)
- Documentación OpenAPI/Swagger

### Infrastructure

- Docker + Docker Compose (postgres, redis, django, celery, jenkins, sonarqube)
- Pipeline CI/CD con Jenkins
- Pruebas E2E con Playwright
- Pruebas de carga con Locust
- Análisis estático con SonarQube
