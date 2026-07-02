# Buenas Prácticas de Seguridad

## Contraseñas

- Almacenadas con el hasher por defecto de Django (PBKDF2 + SHA256)
- Mínimo 8 caracteres
- No almacenadas en logs ni respuestas de API

## Tokens JWT

- Access token: 8 horas de vida
- Refresh token: 7 días, con rotation
- Almacenados en `localStorage` (frontend)
- En producción: considerar cookies HttpOnly + Secure

## Variables de Entorno

- Todas las claves de API y contraseñas via variables de entorno
- Archivo `.env` en `.gitignore`
- Valores por defecto seguros en `settings.py`

## API

- CORS configurado solo para orígenes permitidos
- Validación de entrada en serializers
- Permisos verificados en cada endpoint
- No exponer modelos internos en respuestas

## Base de Datos

- Soft delete: los registros no se eliminan físicamente
- Auditoría de acciones críticas en `AuditLog`
- Índices para consultas frecuentes

## Frontend

- React escapa HTML automáticamente (protección XSS)
- TanStack Query maneja caché de datos del servidor
- Interceptor de Axios para manejo centralizado de errores 401
- No almacenar datos sensibles en sessionStorage

## Dependencias

- Revisar periódicamente con `pip-audit` y `npm audit`
- Mantener dependencias actualizadas
- Usar versiones fijas en `requirements.txt` y `package.json`
