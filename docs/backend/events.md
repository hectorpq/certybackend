# Eventos (App `events`) e Instructores (App `instructors`)

## Modelos

### `Event` (`events/models.py`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `category` | FK `EventCategory` | Categoría del evento |
| `created_by` | FK `User` | Usuario que creó el evento |
| `instructor` | FK `Instructor` (nullable) | Instructor principal |
| `name` | `CharField(200)` | Nombre del evento |
| `description` | `TextField` | Descripción detallada |
| `event_date` | `DateField` | Fecha del evento |
| `end_date` | `DateField` (nullable) | Fecha de fin |
| `duration_hours` | `IntegerField` (nullable) | Duración en horas |
| `location` | `CharField(200)` | Ubicación |
| `status` | `CharField(20)` | Estado: `draft`, `active`, `finished`, `cancelled` |
| `is_active` | `BooleanField` | Evento activo/inactivo |
| `auto_send_certificates` | `BooleanField` | Envío automático de certificados |
| `template` | FK `Template` (nullable) | Plantilla asociada |
| `invitation_message` | `TextField` | Mensaje de invitación |
| `is_public` | `BooleanField` | Evento público/privado |
| `max_capacity` | `IntegerField` (nullable) | Capacidad máxima |
| `name_font_size` | `IntegerField` (default: 24) | Tamaño de fuente en certificados |
| `name_x`, `name_y` | `IntegerField` | Coordenadas del nombre |
| `template_image` | `CharField` | Imagen de plantilla (legacy) |

**Herencia:** `SoftDeleteMixin` — soporta borrado lógico con marcas de tiempo (`deleted_at`, `deleted_by`).

### `EventCategory` (`events/models.py`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | `CharField(100, unique)` | Nombre de la categoría |
| `description` | `TextField` | Descripción |

### `Enrollment` (`events/models.py`)

Inscripción de un participante a un evento.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `participant` | FK `Participant` | Participante inscrito |
| `event` | FK `Event` | Evento |
| `status` | `CharField` | `pending`, `confirmed`, `cancelled` |
| `attendance` | `BooleanField` | Asistencia marcada |
| `grade` | `DecimalField` (nullable) | Calificación |
| `notes` | `TextField` | Notas adicionales |
| `certificate_sent` | `BooleanField` | Certificado enviado |
| `certificate_sent_at` | `DateTimeField` (nullable) | Fecha de envío |
| `certificate_sent_method` | `CharField` | Método de envío |

### `EventInvitation` (`events/models.py`)

Invitación a un evento con token único.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `event` | FK `Event` | Evento |
| `participant` | FK `Participant` (nullable) | Participante (si ya existe) |
| `email` | `EmailField` | Email del invitado |
| `token` | `CharField(64, unique)` | Token UUID único |
| `status` | `CharField` | `pending`, `sent`, `accepted`, `rejected`, `expired` |
| `expires_at` | `DateTimeField` (nullable) | Fecha de expiración (7 días) |

### `Instructor` (`instructors/models.py`)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `full_name` | `CharField(150)` | Nombre completo |
| `email` | `EmailField(unique)` | Correo electrónico |
| `phone` | `CharField(20)` | Teléfono |
| `specialty` | `CharField(200)` | Especialidad |
| `bio` | `TextField` | Biografía |
| `signature_url` | `TextField` | URL de firma (legacy) |
| `signature_image` | `ImageField` | Imagen de firma (PNG/JPG con fondo transparente) |
| `is_active` | `BooleanField` | Activo/inactivo |

**Herencia:** `SoftDeleteMixin` — soporta borrado lógico.

## Endpoints REST

### Eventos (`/api/events/`)

- `GET /api/events/` — Lista paginada de eventos (filtrable por `status`, `category`, `search`)
- `POST /api/events/` — Crear evento (`created_by` se asigna automáticamente)
- `GET /api/events/{id}/` — Detalle del evento
- `PUT /api/events/{id}/` — Actualizar evento completo
- `PATCH /api/events/{id}/` — Actualizar evento parcial
- `DELETE /api/events/{id}/` — Eliminar evento (borrado lógico)

### Acciones de Evento

- `GET /api/events/{id}/participants/` — Listar participantes del evento con estado de certificado
- `POST /api/events/{id}/enroll/` — Inscribir participante al evento (por `participant_id` o `participant_email`)
- `POST /api/events/{id}/certificates/generate/` — Generar certificados para asistentes
- `POST /api/events/{id}/certificates/send/` — Enviar certificados del evento
- `GET /api/events/{id}/deliveries/` — Registros de entrega del evento
- `GET /api/events/{id}/stats/` — Estadísticas del evento
- `GET /api/events/{id}/invitations/` — Listar invitaciones
- `POST /api/events/{id}/invitations/send/` — Enviar invitaciones (desde archivo o lista de emails)
- `POST /api/events/{id}/invitations/send-all/` — Reenviar todas las invitaciones pendientes
- `POST /api/events/{id}/finalize/` — Finalizar evento (marca como `finished`, opcionalmente envía certificados)
- `GET /api/events/{id}/changelog/` — Historial de cambios
- `POST /api/events/{id}/restore/` — Restaurar evento eliminado

### Instructores (`/api/instructors/`)

- `GET /api/instructors/` — Listar instructores (búsqueda por nombre, email, especialidad)
- `POST /api/instructors/` — Crear instructor
- `GET /api/instructors/{id}/` — Detalle
- `PUT /api/instructors/{id}/` — Actualizar
- `DELETE /api/instructors/{id}/` — Eliminar
- `GET /api/instructors/{id}/changelog/` — Historial de cambios
- `POST /api/instructors/{id}/restore/` — Restaurar

### Inscripciones (`/api/enrollments/`)

- `GET /api/enrollments/` — Listar inscripciones
- `POST /api/enrollments/` — Inscribir participante
- `DELETE /api/enrollments/{id}/` — Eliminar inscripción
- `PATCH /api/enrollments/{id}/attendance/` — Marcar asistencia

### Invitaciones (públicas)

- `GET /api/invitations/{token}/` — Obtener detalles de invitación (público)
- `POST /api/invitations/{token}/accept/` — Aceptar invitación (participante ya registrado)
- `POST /api/invitations/{token}/register/` — Registrarse y aceptar (nuevo participante)
