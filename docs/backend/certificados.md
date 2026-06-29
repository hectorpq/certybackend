# Certificados (App `certificados`)

## Modelos

### `Certificate`

Modelo principal que representa un certificado emitido a un participante por un evento.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `participant` | FK `Participant` | Participante al que pertenece el certificado |
| `event` | FK `Event` | Evento asociado |
| `template` | FK `Template` (nullable) | Plantilla usada para el PDF |
| `generated_by` | FK `User` (nullable) | Usuario que generó el certificado |
| `verification_code` | `CharField(50, unique)` | Código único de verificación (formato SHA-256 truncado) |
| `pdf_url` | `TextField` | Ruta al archivo PDF generado |
| `status` | `CharField(20)` | Estado: `pending`, `generated`, `sent`, `failed` |
| `expires_at` | `DateTimeField` (nullable) | Fecha de expiración (1 año desde emisión) |
| `issued_at` | `DateTimeField` (auto) | Fecha de emisión |
| `updated_at` | `DateTimeField` (auto) | Última actualización |

**Restricción:** `unique_together = (participant, event)` — un participante no puede tener dos certificados para el mismo evento.

**Herencia:** `SoftDeleteMixin` — soporta borrado lógico con `is_deleted`, `deleted_at` y `deleted_by`.

**Historial:** `HistoricalRecords` — cada cambio queda registrado con quién, cuándo y qué cambió (accesible via `certificate.history.all()`).

### `Template`

Modelo para las plantillas visuales de los certificados.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | `CharField(100)` | Nombre de la plantilla |
| `category` | `CharField(100)` | Categoría (opcional) |
| `background_image` | `ImageField` | Imagen de fondo (PNG/JPG) |
| `layout_config` | `JSONField` | Configuración JSON de posiciones: `participant_name`, `event_name`, `event_date`, `verification_code`, `qr_code`, `signature` |
| `is_active` | `BooleanField` | Plantilla activa/inactiva |
| `font_color`, `font_family`, `font_size` | Campos planos | Configuración tipográfica del nombre |
| `x_coord`, `y_coord` | `FloatField` | Coordenadas de posición del nombre (en pulgadas) |

## Endpoints REST

### Certificados (`/api/certificates/`)

- `GET /api/certificates/` — Lista paginada de certificados (admin/coordinador ve todos, participante solo los suyos)
- `POST /api/certificates/` — Crear certificado manualmente
- `GET /api/certificates/{id}/` — Detalle del certificado con historial de entregas
- `PATCH /api/certificates/{id}/` — Actualizar certificado
- `DELETE /api/certificates/{id}/` — Eliminar certificado (borrado lógico)

### Acciones de Certificado

- `POST /api/certificates/{id}/generate/` — Generar PDF del certificado
    - Body opcional: `{"template_id": "uuid"}`
    - Cambia estado de `pending` a `generated`
- `POST /api/certificates/{id}/deliver/` — Entregar certificado
    - Body requerido: `{"method": "email|whatsapp|link"}`
    - Body opcional: `{"recipient": "email o teléfono"}`
- `GET /api/certificates/{id}/history/` — Historial de entregas del certificado
- `POST /api/certificates/{id}/retry/` — Reintentar entrega fallida
- `GET /api/certificates/{id}/changelog/` — Historial de cambios del certificado
- `POST /api/certificates/{id}/restore/` — Restaurar certificado eliminado (solo admin)
- `GET /api/certificates/export/` — Exportar certificados a CSV/Excel (solo admin)
- `GET /api/certificates/verify/?code=XXXX` — Verificar autenticidad (público, no requiere auth)

### Entregas (`/api/deliveries/`)

- `GET /api/deliveries/` — Listar registros de entrega (solo admin, filtrable por `certificate_id`)
- `GET /api/deliveries/{id}/` — Detalle de registro de entrega

### Certificados - Masivo

- `POST /api/certificates/preview/` — Previsualizar datos del Excel (no crea nada)
- `POST /api/certificates/process/` — Procesar registros editados y crear certificados
- `POST /api/certificates/generate-bulk/` — Generar certificados masivamente desde Excel (multipart: `excel_file`, `template_image`, `event_id`)

### Plantillas (`/api/templates/`)

- `GET /api/templates/` — Listar plantillas
- `POST /api/templates/` — Crear plantilla
- `GET /api/templates/{id}/` — Detalle de plantilla
- `PUT /api/templates/{id}/` — Actualizar plantilla
- `DELETE /api/templates/{id}/` — Eliminar plantilla
- `POST /api/templates/{id}/upload-image/` — Subir imagen de fondo
- `POST /api/templates/{id}/upload-signature/` — Subir firma del instructor
- `GET /api/templates/{id}/preview/` — Previsualizar plantilla
- `GET /api/templates/{id}/changelog/` — Historial de cambios
- `POST /api/templates/{id}/restore/` — Restaurar plantilla eliminada

## Flujo de Emisión de un Certificado

- **Creación:** Se crea el registro `Certificate` con estado `pending` y se genera automáticamente un `verification_code` único basado en SHA-256 del participante + evento + timestamp.
- **Generación de PDF:** Se invoca `POST /certificates/{id}/generate/`. El servicio `PDFService` toma la plantilla asociada, renderiza el nombre del participante, evento, fecha, código QR de verificación y firma del instructor sobre la imagen de fondo. El PDF se guarda en `certificates/pdfs/`.
- **Distribución:** Se invoca `POST /certificates/{id}/deliver/` con el método deseado. Se crea un `DeliveryLog` que registra el intento. Si el envío es exitoso, el certificado pasa a estado `sent`; si falla, queda en `failed` y se puede reintentar.
- **Verificación Pública:** Cualquier persona puede verificar la autenticidad del certificado mediante `GET /api/certificates/verify/?code=XXXX`. El endpoint es público y retorna los datos del certificado si es válido.
