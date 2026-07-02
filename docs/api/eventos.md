# Eventos — `events`

## Modelo `Event`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | CharField(255) | Nombre del evento |
| `description` | TextField | Descripción |
| `event_date` | DateField | Fecha del evento |
| `end_date` | DateField (nullable) | Fecha de fin |
| `duration_hours` | FloatField (nullable) | Duración en horas |
| `location` | CharField | Ubicación |
| `status` | CharField(choices) | `draft`, `active`, `finished`, `cancelled` |
| `category` | FK(EventCategory, nullable) | Categoría |
| `instructor` | FK(Instructor, nullable) | Instructor asociado |
| `template` | FK(Template, nullable) | Plantilla por defecto |
| `is_public` | BooleanField | Visible públicamente |
| `max_capacity` | IntegerField (nullable) | Capacidad máxima |

**Configuración visual del certificado** (campos en Event):
- `name_font_size`, `name_x`, `name_y`, `font_color`, `template_image`

## Modelo `Enrollment`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `participant` | FK(Participant) | Participante inscrito |
| `event` | FK(Event) | Evento |
| `status` | CharField | `enrolled`, `confirmed`, `cancelled` |
| `attendance` | BooleanField | Asistencia registrada |
| `grade` | FloatField (nullable) | Nota/calificación |
| `notes` | TextField | Notas adicionales |

## Modelo `EventInvitation`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `event` | FK(Event) | Evento |
| `participant` | FK(Participant, nullable) | Participante (si ya existe) |
| `email` | EmailField | Email del invitado |
| `token` | UUIDField (unique) | Token único de invitación |
| `status` | CharField | `pending`, `accepted`, `declined`, `expired` |

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| GET/POST | `/api/events/` | Lista / Crear |
| GET/PATCH/DELETE | `/api/events/{id}/` | Detalle / Actualizar / Eliminar |
| POST | `/api/events/{id}/restore/` | Restaurar |
| GET | `/api/events/{id}/participants/` | Participantes con estado de certificado |
| POST | `/api/events/{id}/enroll/` | Inscribir participante |
| POST | `/api/events/{id}/certificates/generate/` | Generar certificados |
| POST | `/api/events/{id}/certificates/send/` | Enviar certificados |
| GET | `/api/events/{id}/stats/` | Estadísticas |
| POST | `/api/events/{id}/finalize/` | Finalizar evento |
| GET/POST | `/api/events/{id}/invitations/` | Invitaciones |
| POST | `/api/events/{id}/invitations/send/` | Enviar invitaciones |
