# Envío de Correos (`services/email_service.py`)

## Servicio de Email (`EmailService`)

Servicio que utiliza la **API de SendGrid** para el envío de correos electrónicos transaccionales.

### Métodos Principales

- `send_email(subject, text, recipient_email)` — Envía un correo genérico en texto plano.
- `send_certificate(certificate, recipient_email)` — Envía el certificado PDF por correo al participante. Adjunta el archivo PDF codificado en base64 si existe. El asunto incluye el nombre del evento y el cuerpo contiene: nombre del participante, evento, fecha, código de verificación, URL del PDF y fecha de expiración.
- `send_bulk_certificates(certificates, recipient_map)` — Envía certificados en lote. Por cada certificado, determina el destinatario (desde `recipient_map` o desde `certificate.participant.email`).

### Tareas Asíncronas (`services/tasks.py`)

Las tareas de Celery evitan que el envío de correos masivos bloquee los hilos de respuesta de la API:

- `send_certificate_email_task(certificate_id, recipient_email)` — Tarea `@shared_task` con hasta **3 reintentos** y **60 segundos** de espera entre reintentos. Obtiene el certificado por ID, invoca `EmailService.send_certificate()` y reintenta automáticamente si falla.
- `send_bulk_certificates_task(event_id, method="email")` — Envía todos los certificados de un evento de forma asíncrona.

## Flujo de Envío Masivo

- **Inicio:** El usuario (admin/coordinador) solicita el envío masivo desde el frontend o la API (`POST /events/{id}/certificates/send/`).
- **Encolamiento:** La solicitud crea las tareas Celery en Redis y retorna inmediatamente sin bloquear.
- **Procesamiento en segundo plano:** Los workers de Celery recogen las tareas de la cola y ejecutan `send_certificate_email_task` o `send_bulk_certificates_task` según corresponda.
- **Registro:** Cada intento de envío se registra en `DeliveryLog` con el método, destinatario, estado (`success`/`failed`) y mensaje de error si falla.
- **Reintentos:** Si un envío falla, la tarea Celery lo reintenta automáticamente hasta 3 veces. Si persiste el error, el certificado queda en estado `failed` y puede ser reintentado manualmente.
- **Notificación:** El frontend puede consultar el estado de las entregas via `GET /certificates/{id}/history/`.
