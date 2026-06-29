# Envío de WhatsApp (`services/whatsapp_service.py`)

## Servicio de WhatsApp (`WhatsAppService`)

Servicio que utiliza la **Meta WhatsApp Cloud API** (v19.0) para enviar notificaciones con certificados a través de WhatsApp. El tier gratuito permite hasta 1,000 mensajes por mes.

### Configuración

Requiere dos variables de entorno:

- `META_WHATSAPP_TOKEN` — Token de acceso generado en Facebook Developers.
- `META_WHATSAPP_PHONE_ID` — ID del número de teléfono empresarial configurado en Meta.

### Métodos Principales

- `send_certificate(certificate, phone_number)` — Envía un mensaje de texto con los detalles del certificado: nombre del evento, código de verificación y URL del PDF. Limpia automáticamente el número de teléfono (elimina `+`, espacios y guiones).
- `send_bulk_certificates(certificates, phone_map)` — Envía certificados en lote. Usa `phone_map` si se proporciona, o el número de teléfono del participante (`certificate.participant.phone`).

### Formato del Mensaje

```
Hola {nombre}!

Tu certificado del evento "{evento}" está listo.

Detalles:
- Código de verificación: XXXX-XXXX
- PDF: {url_del_pdf}

Sistema de Certificados
```

### Tolerancia a Fallos

- Si el servicio no está configurado (token o phone_id vacíos), retorna un error descriptivo sin lanzar excepción.
- Si el participante no tiene número de teléfono registrado, retorna error indicando que no se proporcionó número.
- Los errores de la API de Meta se capturan y registran en los logs.

## Tareas Asíncronas

Actualmente el envío por WhatsApp se realiza de forma síncrona en el contexto de la petición. Para envíos masivos, se recomienda envolverlo en una tarea Celery similar a `send_certificate_email_task` cuando se requiera escalar.

### Singleton

El servicio utiliza un patrón singleton mediante la función `get_whatsapp_service()` que retorna una instancia única reutilizable.
