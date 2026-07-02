# Diagrama de Base de Datos

## Modelo Entidad-Relación

```
User (users)
├── id, email, full_name, role [admin|coordinador|participante]
├── is_active, is_staff
├── created_at, updated_at
├── audit_logs → AuditLog
├── delivery_logs → DeliveryLog
├── created_events → Event
├── created_participants → Participant
├── created_templates → Template
├── created_enrollments → Enrollment
└── created_certificates → Certificate

Event (events)
├── id, name, description, location
├── event_date, end_date, duration_hours
├── status [draft|active|finished|cancelled]
├── category → EventCategory
├── instructor → Instructor
├── template → Template
├── font_color, name_font_size, name_x, name_y (template config)
├── is_public, max_capacity
├── auto_send_certificates, invitation_message
├── is_deleted, deleted_at, deleted_by → User
├── created_by → User
├── created_at, updated_at
├── enrollments → Enrollment
├── invitations → EventInvitation
└── certificates → Certificate

Participant (participants)
├── id, document_id, first_name, last_name
├── full_name (computado)
├── email, phone, is_active
├── is_deleted, deleted_at, deleted_by → User
├── created_by → User
├── created_at, updated_at
├── enrollments → Enrollment
└── certificates → Certificate

Enrollment (events)
├── id, participant → Participant, event → Event
├── status [enrolled|confirmed|cancelled]
├── attendance (bool), grade, notes
├── invitation → EventInvitation
├── invitation_sent, certificate_sent
├── certificate_sent_at, certificate_sent_method
├── created_by → User
└── enrolled_at

EventInvitation (events)
├── id, event → Event, participant? → Participant, email
├── token (UUID, único)
├── status [pending|accepted|declined|expired|cancelled]
├── expires_at, sent_at, responded_at
├── created_by → User
└── created_at

Certificate (certificados)
├── id, participant → Participant, event → Event
├── template? → Template
├── status [pending|generated|sent|failed]
├── verification_code (único, 20 chars)
├── pdf_url, expires_at
├── generated_by → User
├── issued_at, updated_at
└── deliveries → DeliveryLog

Template (certificados)
├── id, name, category
├── background_image (ImageField)
├── background_url, layout_config (JSON)
├── font_color, font_family, font_size
├── x_coord, y_coord
├── is_active, created_by → User
├── created_at, updated_at
├── signature_image (ImageField)
└── preview_url

Instructor (instructors)
├── id, full_name, email, phone
├── specialty, bio
├── signature_image, signature_url
├── created_by → User
├── created_at, updated_at
└── events → Event

DeliveryLog (deliveries)
├── id (BigAutoField), certificate → Certificate
├── sent_by → User
├── delivery_method [email|whatsapp|link]
├── recipient, status [success|error|pending]
├── error_message, sent_at, updated_at
├── índices: status, delivery_method, certificate

AuditLog (api)
├── id, action [6 tipos]
├── user → User, certificate → Certificate
├── ip_address, details (JSON)
├── timestamp
├── índices: action, timestamp, user

EventCategory (events)
├── id, name, description
└── created_by → User
```

## Convenciones del Esquema

- **Soft Delete:** Los modelos principales tienen `is_deleted`, `deleted_at`, `deleted_by`
- **Timestamps:** `created_at` (auto_now_add), `updated_at` (auto_now)
- **Índices:** status, action, certificate, delivery_method, timestamp, user
- **Orden por defecto:** `-created_at` o `-sent_at` (más reciente primero)
- **Claves foráneas:** `CASCADE` en Certificate→Participant/Event; `SET_NULL` en AuditLog→User

## Consultas Clave Indexadas

| Consulta | Índice |
|----------|--------|
| Certificados por status | Index en `Certificate.status` |
| Entregas por método | Index en `DeliveryLog.delivery_method` |
| Auditoría por acción | Index en `AuditLog.action` |
| Historial por usuario | Index en `AuditLog.user` |
| Búsqueda temporal | Index en `AuditLog.timestamp` |
