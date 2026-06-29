# Serializadores — `api/serializers.py`

Lista completa de serializadores organizados por modelo/uso.

## Eventos

| Serializer | Uso |
|------------|-----|
| `EventSerializer` | CRUD completo de eventos. Incluye `template_name`, `instructor_name`, `status_display`, `deleted_by_detail` como campos de solo lectura |
| `EventSimpleSerializer` | Versión ligera: solo `id`, `name`, `status` |

## Participantes

| Serializer | Uso |
|------------|-----|
| `ParticipantSerializer` | CRUD completo. `full_name` read-only (se computa), `deleted_by_detail` como SerializerMethodField |

## Usuarios

| Serializer | Uso |
|------------|-----|
| `UserSerializer` | Datos públicos del usuario (id, email, full_name, role, is_staff, is_active) |
| `UserAuthSerializer` / `UserLoginSerializer` | Validación de credenciales login. Autentica y retorna el objeto user |
| `UserRegisterSerializer` | Registro con password_confirm. Valida que las contraseñas coincidan, crea el usuario con `create_user` |

## Certificados

| Serializer | Uso |
|------------|-----|
| `CertificateListSerializer` | Lista con `participant_info` (id, full_name, email, phone) y `event` (id, name, event_date, category) anidados |
| `CertificateDetailSerializer` | Igual que List + `delivery_history` (DeliveryLogSerializer anidado) + datos extendidos del evento (end_date, description, location, duration_hours, instructor_name) |
| `CertificateCreateSerializer` | Creación (fields `__all__`) |
| `CertificateGenerateSerializer` | `participant_id`, `event_id`, `template_id` |
| `CertificateDeliverSerializer` | `method` (email/whatsapp/link), `recipient` |
| `CertificateRetrySerializer` | `method` opcional (reintento) |

## Plantillas

| Serializer | Uso |
|------------|-----|
| `TemplateSerializer` | Full detail con `background_image_url` calculado (absolute URI) |
| `TemplateCreateSerializer` | Creación (name, category, is_active, font fields) |
| `TemplateUpdateSerializer` | Actualización parcial (mismos campos que Create) |

## Inscripciones e Invitaciones

| Serializer | Uso |
|------------|-----|
| `EnrollmentSerializer` | Inscripción completa con attendance, grade, notes, certificate_sent |
| `EnrollmentCreateSerializer` | Creación: `participant_id`, `attendance`, `grade`, `notes` |
| `EventEnrollSerializer` | Inscribir por `participant_id` o `participant_email` |
| `EventInvitationSerializer` | Invitación con `status_display`, `participant_name`, `event_name` |
| `InvitationDetailSerializer` | Vista pública de invitación con datos del evento expandidos |
| `InvitationRegisterSerializer` | Registro desde invitación: `first_name`, `last_name`, `phone`, `password` |

## Instructores

| Serializer | Uso |
|------------|-----|
| `InstructorSerializer` | CRUD completo (fields `__all__`) |

## DeliveryLog

| Serializer | Uso |
|------------|-----|
| `DeliveryLogSerializer` | Full detail con `status_display`, `delivery_method_display`, `is_successful`, `is_failed`, `is_pending` |

## Bulk / Importación Masiva

| Serializer | Uso |
|------------|-----|
| `ExcelBulkImportSerializer` | Solo `excel_file` (FileField) |
| `BulkProcessDataSerializer` | Array de registros con `full_name`, `email`, `document_id`, `event_name` |
| `EventGenerateCertificatesSerializer` | `participant_ids` opcional |
| `EventSendCertificatesSerializer` | `method` + `participant_ids` opcional |
| `EventSendInvitationsSerializer` | `file` (CSV/Excel) o `emails` (JSON) |
| `EventFinalizeSerializer` | `send_certificates` (boolean) |

## Auditoría

| Serializer | Uso |
|------------|-----|
| `AuditLogSerializer` | Log completo con `user_email`, `action_display`, `ip_address` como CharField |

## Historial de Cambios

| Serializer | Uso |
|------------|-----|
| `ChangelogSerializer` | Historial de cambios vía `django-simple-history`. `history_type_display` detecta creación/edición/eliminación/restauración lógica. `fields_changed` muestra diff de valores anterior/nuevo |

## Alias de Retrocompatibilidad

```python
CertificateSerializer = CertificateListSerializer
StudentSerializer = ParticipantSerializer  # alias backward compat
```
