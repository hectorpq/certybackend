# Certy — Sistema de Gestión y Entrega Masiva de Certificados

**Certy** automatiza la emisión, personalización y distribución de certificados académicos. Diseñado para instituciones educativas y organizadores de eventos, cubre todo el ciclo: desde la creación del evento y el diseño de la plantilla visual hasta la generación del PDF con código QR y la entrega por email, WhatsApp o enlace público.

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Django 5.2 + DRF 3.14 + Python 3.11+ |
| Frontend | React 18 + Vite 5 + TypeScript 5 + TailwindCSS 3 |
| Base de datos | PostgreSQL 15 |
| Cache / Broker | Redis 7 + Celery |
| PDF | ReportLab + qrcode (Pillow) |
- Correo: SendGrid API
- WhatsApp: Meta Cloud API
- Tests E2E: Playwright
- Calidad: SonarQube
- CI/CD: Jenkins + Docker

## Rol del Usuario

| Rol | Acceso |
|-----|--------|
| **admin** | Total: auditoría, exportación, gestión de usuarios, configuración |
| **coordinador** | Operativo: eventos, certificados, participantes, instructores |
| **participante** | Lectura propia: certificados y eventos donde está inscrito |

## Enlaces Rápidos

- [Introducción y propósito del sistema](introduccion.md)
- [Arquitectura C4 y decisiones técnicas](arquitectura/overview.md)
- [Catálogo de requisitos](requisitos/requisitos-funcionales.md)
- [Documentación de la API](api/autenticacion.md)
- [Guía de instalación y despliegue](despliegue/instalacion.md)
- [Manuales de usuario](usuario/administrador.md)
- [Checklist de auditoría SDLC](auditoria/checklist-sdlc.md)
