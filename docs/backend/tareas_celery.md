# Tareas Celery Asíncronas — `services/tasks.py` + `config/celery.py`

## Configuración de Celery (`config/celery.py`)

```python
app = Celery("scad")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

- **Nombre de la aplicación:** `scad`
- **Namespace de configuración:** `CELERY_` (ej. `CELERY_BROKER_URL`)
- **Auto-descubrimiento:** Busca tareas en `tasks.py` de todas las apps instaladas

### Variables de entorno requeridas

- `REDIS_URL` — URL de conexión a Redis (broker + backend de resultados)

## Tareas (`services/tasks.py`)

### `send_certificate_email_task(certificate_id, recipient_email)`

- **Cola:** por defecto
- **Propósito:** Enviar un certificado por email de forma asíncrona
- **Comportamiento:** Obtiene el certificado con `select_related`, llama a `EmailService.send_certificate()`, reintenta hasta 3 veces con 60s de espera entre intentos
- **Error:** Si `send_certificate()` retorna `success=False`, lanza `ValueError` provocando retry

### `generate_certificate_pdf_task(certificate_id)`

- **Cola:** por defecto
- **Propósito:** Generar PDF para un certificado de forma asíncrona
- **Comportamiento:** Obtiene certificado con `select_related("participant", "event", "template")`, llama a `PDFService.generate_certificate_pdf()`, guarda `pdf_url` en el certificado si tiene éxito
- **Reintentos:** 2 veces con 120s de espera

### `send_bulk_certificates_task(event_id, method="email")`

- **Propósito:** Enviar todos los certificados de un evento en lote
- **Comportamiento:** Filtra `Certificate` por `event_id`, obtiene lista con `select_related`, llama a `EmailService.send_bulk_certificates()`
- **Nota:** Actualmente solo soporta método `email`

## Cómo Ejecutar el Worker

```bash
# Worker principal
celery -A config worker -l info

# Worker con queues específicas
celery -A config worker -l info -Q celery

# Monitor (flower)
celery -A config flower
```

## Variables de Entorno Relacionadas

| Variable | Propósito | Ejemplo |
|----------|-----------|---------|
| `REDIS_URL` | Conexión a Redis (broker) | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Override explícito del broker | (opcional, usa REDIS_URL) |
