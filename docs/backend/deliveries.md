# Entregas — `deliveries`

## Modelo `DeliveryLog` (`deliveries/models.py`)

Registra cada intento de entrega de un certificado, sea por email, WhatsApp o enlace.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `BigAutoField PK` | Identificador único |
| `certificate` | `FK(Certificate, CASCADE)` | Certificado entregado |
| `sent_by` | `FK(User, SET_NULL)` | Usuario que realizó la entrega |
| `delivery_method` | `CharField(choices)` | Método: `email`, `whatsapp`, `link` |
| `recipient` | `CharField(200)` | Destinatario (email o número) |
| `status` | `CharField(choices)` | Estado: `success`, `error`, `pending` |
| `error_message` | `TextField` | Mensaje de error si falló |
| `sent_at` | `DateTimeField(auto_now_add)` | Fecha/hora del envío |
| `updated_at` | `DateTimeField(auto_now)` | Última actualización |

### Propiedades

- `is_successful` → `status == "success"`
- `is_failed` → `status == "error"`
- `is_pending` → `status == "pending"`
- `get_delivery_icon()` — Emoji según método
- `get_status_icon()` — Emoji según estado

### Índices

- `status`
- `delivery_method`
- `certificate`

### Orden por Defecto

`-sent_at` (más reciente primero)

## Endpoint

- `GET /api/deliveries/` — Lista de entregas (ReadOnly). Filtrable por `certificate_id`.
