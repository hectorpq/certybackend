# Preguntas Frecuentes (FAQ)

## General

### ¿Qué es Certy?
Certy es un sistema web para la gestión y entrega masiva de certificados académicos, permitiendo automatizar la emisión, personalización y distribución por email, WhatsApp y enlace público.

### ¿Quiénes pueden usar Certy?
Instituciones educativas, organizadores de eventos, y cualquier entidad que necesite emitir certificados en volumen.

## Técnico

### ¿Qué stack tecnológico usa?
Django 5.2 + DRF 3.14 (backend), React 18 + Vite + TypeScript (frontend), PostgreSQL 15 (base de datos), Redis + Celery (tareas asíncronas).

### ¿Cómo ejecuto el proyecto localmente?
Ver [Instalación](../despliegue/instalacion.md) y [Setup Backend](../setup/backend.md).

### ¿Cómo ejecuto las pruebas?
```bash
cd backend
pytest
```

### ¿Dónde está la documentación de la API?
En [Swagger / OpenAPI](../api/swagger.md).

## Usuarios

### ¿Cómo creo un evento?
Ver manual de [Coordinador](../usuario/coordinador.md).

### ¿Cómo verifico un certificado?
Usa el enlace público de verificación o escanea el código QR en el PDF.

### ¿Qué hago si no recibo mi certificado?
Revisa tu bandeja de spam o contacta al coordinador del evento.

## Seguridad

### ¿Cómo se protegen los datos?
JWT para autenticación, OAuth para integraciones, roles y permisos granulares, y auditoría de acciones críticas.

### ¿Los certificados son verificables?
Sí, cada certificado incluye un código QR único que redirige a la página de verificación.

## Mantenimiento

### ¿Cada cuánto se hacen respaldos?
Los respaldos de base de datos se realizan diariamente de forma automatizada.

### ¿Cómo actualizo el sistema?
Ver [Actualización](../mantenimiento/actualizacion.md).
