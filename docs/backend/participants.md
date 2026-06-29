# Participantes (App `participants`)

## Modelo `Participant`

Modelo que representa a un participante/estudiante en el sistema.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `BigAutoField` (PK) | Identificador único |
| `document_id` | `CharField(20, unique)` | Documento de identidad (DNI, cédula, pasaporte) — único en el sistema |
| `first_name` | `CharField(100)` | Nombre |
| `last_name` | `CharField(100)` | Apellido |
| `full_name` | `@property` | Propiedad computada: `"{first_name} {last_name}"` |
| `email` | `EmailField(unique)` | Correo electrónico — único |
| `phone` | `CharField(20)` | Teléfono (opcional) |
| `is_active` | `BooleanField` | Estado activo/inactivo |
| `created_by` | FK `User` (nullable) | Usuario que registró al participante |
| `created_at` | `DateTimeField` (auto) | Fecha de registro |
| `updated_at` | `DateTimeField` (auto) | Última actualización |

**Herencia:** `SoftDeleteMixin` — soporta borrado lógico con marcas de tiempo.

**Índices:** `is_active`, `document_id`, `email`, `is_deleted`.

**Historial:** `HistoricalRecords` — cada cambio queda registrado.

## Endpoints REST

- `GET /api/participants/` — Lista paginada de participantes (búsqueda por nombre, email, documento)
    - Parámetros: `search`, `is_active`, `ordering`
- `POST /api/participants/` — Crear participante
    - `document_id` y `email` deben ser únicos
    - `created_by` se asigna automáticamente
- `GET /api/participants/{id}/` — Detalle del participante
- `PUT /api/participants/{id}/` — Actualizar participante (todos los campos)
- `PATCH /api/participants/{id}/` — Actualización parcial
- `DELETE /api/participants/{id}/` — Eliminar participante (borrado lógico)
- `POST /api/participants/import_students/` — Importación masiva desde Excel/CSV (solo admin)
    - Acepta columnas: `document_id`/`documento`, `email`, `first_name`/`last_name`/`full_name`, `phone`
    - Los nombres de columna son flexibles (mayúsculas/minúsculas, español/inglés)
- `GET /api/participants/{id}/changelog/` — Historial de cambios
- `POST /api/participants/{id}/restore/` — Restaurar participante eliminado (solo admin)

## Importación Masiva

El endpoint `POST /api/participants/import_students/` permite importar participantes desde archivos Excel (`.xlsx`, `.xls`) o CSV.

**Columnas soportadas:**

- `document_id` o `documento` — requerido
- `email` — requerido
- `first_name`/`last_name` o `nombre`/`apellido` o `full_name`/`nombre_completo` — al menos una combinación
- `phone` o `telefono` — opcional

El sistema tolera nombres de columna en español o inglés. Los errores por fila no detienen el procesamiento de las demás.

!!! note
    La lógica de indexación se basa en los campos `document_id` y `email` con restricciones `unique` a nivel de base de datos, garantizando que no existan duplicados.
