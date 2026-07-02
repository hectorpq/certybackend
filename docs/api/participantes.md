# Participantes — `participants`

## Modelo `Participant`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | AutoField | PK |
| `document_id` | CharField(50) | Documento de identidad (único) |
| `first_name` | CharField(100) | Nombres |
| `last_name` | CharField(100) | Apellidos |
| `full_name` | (property) | Computado: `first_name + last_name` |
| `email` | EmailField | Email |
| `phone` | CharField(20) | Teléfono |
| `is_active` | BooleanField | Activo |
| `is_deleted` | BooleanField | Soft delete |
| `deleted_at` | DateTimeField (nullable) | Fecha de eliminación |
| `created_by` | FK(User) | Usuario creador |
| `created_at` | DateTimeField | Fecha de creación |

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/participants/` | Lista paginada (filtros: search, is_active) |
| POST | `/api/participants/` | Crear |
| GET | `/api/participants/{id}/` | Detalle |
| PATCH | `/api/participants/{id}/` | Actualizar |
| DELETE | `/api/participants/{id}/` | Soft delete |
| POST | `/api/participants/{id}/restore/` | Restaurar |
| POST | `/api/participants/import_participants/` | Importar desde Excel |

## Importación Masiva

POST `/api/participants/import_participants/` (multipart: `file`)

- Acepta `.xlsx` y `.csv`
- Columnas requeridas: `full_name`, `email`, `document_id`
- No duplica si el email o document_id ya existen
- Retorna: total_rows, imported, errors[]
