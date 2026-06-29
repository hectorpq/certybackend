# Modelos y Relaciones de Datos

## Diagrama de Relaciones

```
User (users)
  ├── role: admin | coordinador | participante
  ├── audit_logs ← AuditLog (api)
  ├── delivery_logs ← DeliveryLog (deliveries)
  ├── created_certificates → Certificate (certificados)
  ├── created_events → Event (events)
  ├── created_participants → Participant (participants)
  ├── created_templates → Template (certificados)
  └── created_enrollments → Enrollment (events)

Event (events)
  ├── status: draft | active | finished | cancelled
  ├── created_by → User
  ├── instructor? → Instructor (instructors)
  ├── template? → Template (certificados)
  ├── category? → EventCategory (events)
  ├── enrollments → Enrollment (events)
  ├── invitations → EventInvitation (events)
  └── certificates → Certificate (certificados)

Participant (participants)
  ├── full_name (computado: first_name + last_name)
  ├── soft delete: is_deleted, deleted_at, deleted_by
  ├── created_by → User
  ├── enrollments → Enrollment (events)
  └── certificates → Certificate (certificados)

Enrollment (events)
  ├── participant → Participant
  ├── event → Event
  ├── attendance: boolean
  └── status: enrolled | confirmed | cancelled

EventInvitation (events)
  ├── event → Event
  ├── participant? → Participant
  ├── token (UUID, único)
  ├── email
  └── status: pending | accepted | declined | expired | cancelled

Certificate (certificados)
  ├── participant → Participant
  ├── event → Event
  ├── template? → Template
  ├── status: pending | generated | sent | failed
  ├── verification_code (único)
  ├── generated_by → User
  ├── pdf_url
  ├── expires_at
  └── deliveries → DeliveryLog (deliveries)

Template (certificados)
  ├── name, category
  ├── background_image (ImageField)
  ├── background_url (URL)
  ├── layout_config (JSON)
  ├── font_size, font_color, font_family
  ├── x_coord, y_coord
  └── created_by → User

Instructor (instructors)
  ├── full_name, email, phone
  ├── specialty, bio
  └── signature_image (ImageField)

DeliveryLog (deliveries)
  ├── certificate → Certificate
  ├── sent_by → User
  ├── method: email | whatsapp | link
  └── status: success | error | pending

AuditLog (api)
  ├── user? → User
  ├── certificate? → Certificate
  ├── action (6 tipos)
  └── details (JSON)

EventCategory (events)
  ├── name, description
  └── created_by → User
```

## Convenciones Comunes

| Convención | Detalle |
|------------|---------|
| **Soft Delete** | Todos los modelos principales heredan `is_deleted`, `deleted_at`, `deleted_by` |
| **Auditoría** | `created_at`, `updated_at` automáticos via `auto_now_add` / `auto_now` |
| **Orden por defecto** | `-created_at` o `-sent_at` (más reciente primero) |
| **Índices** | Los campos más consultados tienen índices explícitos: status, action, certificate, delivery_method, timestamp, user |
| **User.CREATION** | `User.objects.create_user(password=..., **validated_data)` en vez de `create()` |
