# Análisis de Amenazas

## Identificación de Riesgos

| Amenaza | Impacto | Probabilidad | Mitigación |
|---------|---------|-------------|------------|
| **Filtración de JWT** | Alto | Media | Access token 8h, refresh rotation, HTTPS obligatorio |
| **Inyección SQL** | Alto | Baja | ORM de Django (query parameterized), no SQL raw |
| **XSS (Cross-Site Scripting)** | Medio | Baja | React escapa HTML por defecto, Content-Security-Policy |
| **CSRF** | Medio | Baja | DRF usa tokens CSRF, CORS configurado |
| **Fuga de API keys (SendGrid, WhatsApp)** | Alto | Baja | Almacenadas en variables de entorno, .gitignore |
| **Ataque de fuerza bruta al login** | Medio | Media | Rate limiting (propuesto), contraseñas mín 8 chars |
| **Acceso no autorizado a datos** | Alto | Baja | Permisos por rol validados en cada endpoint |
| **Falsificación de certificados** | Alto | Baja | Código QR de verificación único, endpoint público de verificación |
| **Denegación de servicio (DoS)** | Medio | Media | Gunicorn workers limitados, Celery para tareas pesadas |
| **Exposición de datos en logs** | Bajo | Media | Auditoría no registra contraseñas ni tokens completos |

## Controles Implementados

- [x] Autenticación JWT con refresh rotation
- [x] Roles y permisos por endpoint
- [x] HTTPS (en producción)
- [x] Variables de entorno para secretos
- [x] Validación de entrada en serializers DRF
- [x] CORS configurado
- [x] Soft delete (no pérdida de datos)
- [x] Auditoría de acciones críticas
- [x] Códigos de verificación únicos para certificados

## Controles Propuestos

- [ ] Rate limiting en endpoints de autenticación
- [ ] Headers de seguridad (HSTS, CSP, X-Frame-Options)
- [ ] Escaneo de dependencias con `pip-audit` y `npm audit`
- [ ] Análisis SAST con Bandit (Python)
