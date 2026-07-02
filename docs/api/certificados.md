# Certificados — `certificados`

## Modelo `Certificate`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `participant` | FK(Participant) | Participante al que pertenece |
| `event` | FK(Event) | Evento asociado |
| `template` | FK(Template, nullable) | Plantilla usada para el PDF |
| `status` | CharField(choices) | `pending`, `generated`, `sent`, `failed` |
| `verification_code` | CharField(20, unique) | Código único de verificación |
| `pdf_url` | URLField | URL del PDF generado |
| `expires_at` | DateTimeField(nullable) | Fecha de expiración |
| `generated_by` | FK(User, nullable) | Usuario que generó |
| `issued_at` | DateTimeField | Fecha de emisión |

## Modelo `Template`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | CharField(255) | Nombre de la plantilla |
| `category` | CharField | Categoría (ej. curso, taller) |
| `background_image` | ImageField | Imagen de fondo del certificado |
| `layout_config` | JSONField | Configuración de posiciones (X, Y, fuente) |
| `font_size`, `font_color`, `font_family` | Varios | Estilo del texto |
| `x_coord`, `y_coord` | FloatField | Coordenadas del nombre |

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/certificates/` | Lista paginada |
| POST | `/api/certificates/` | Crear |
| GET | `/api/certificates/{id}/` | Detalle con historial |
| DELETE | `/api/certificates/{id}/` | Eliminar |
| POST | `/api/certificates/{id}/generate/` | Generar PDF |
| POST | `/api/certificates/{id}/deliver/` | Entregar (email/whatsapp/link) |
| GET | `/api/certificates/{id}/history/` | Historial de entregas |
| POST | `/api/certificates/{id}/retry/` | Reintentar entrega |
| GET | `/api/certificates/verify/` | Verificación pública |
| GET | `/api/certificates/export/` | Exportar CSV/Excel |

## Flujo de Emisión

1. Crear certificado con participant + event (status=pending)
2. Opcional: asociar template visual
3. `POST /{id}/generate/` → genera PDF vía PDFService + ReportLab
4. `POST /{id}/deliver/` → envía por método seleccionado
5. Consultar `GET /{id}/history/` para ver estado de entregas
