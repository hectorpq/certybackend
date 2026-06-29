# Auditoría — `AuditLog`

## Modelo `AuditLog` (`api/models.py`)

Registra cada acción relevante del sistema para trazabilidad y cumplimiento.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `action` | `CharField(choices)` | Tipo de acción |
| `user` | `FK(User, SET_NULL)` | Usuario que ejecutó la acción |
| `certificate` | `FK(Certificate, SET_NULL)` | Certificado involucrado (opcional) |
| `ip_address` | `GenericIPAddressField` | Dirección IP del cliente |
| `details` | `JSONField(default=dict)` | Contexto adicional arbitrario |
| `timestamp` | `DateTimeField(auto_now_add)` | Momento del registro |

**Tipos de acción (`ACTION_CHOICES`):**

- `certificate_generated` — Certificado generado
- `certificate_delivered` — Certificado entregado
- `certificate_retried` — Reintento de entrega
- `user_login` — Inicio de sesión exitoso
- `user_login_failed` — Intento de inicio de sesión fallido
- `export_requested` — Exportación de datos solicitada

**Índices:** `action`, `timestamp`, `user`.

**Orden:** `-timestamp` (más reciente primero).

## Helper `api/audit.py`

### `log_action(action, *, user=None, certificate=None, ip_address=None, **details)`

Crea una entrada de auditoría de forma segura. Excepciones silenciadas para no interrumpir el flujo principal.

```python
log_action("certificate_generated", user=request.user, certificate=cert, ip_address=get_client_ip(request))
```

### `get_client_ip(request)`

Extrae la IP real del cliente respetando `X-Forwarded-For`.

## Endpoint

- `GET /api/audit/` — Lista de registros de auditoría (solo admin). Filtrable por `action` y `user_id` (ReadOnlyModelViewSet).
