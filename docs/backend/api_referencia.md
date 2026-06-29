# Referencia Completa de Endpoints API

## Autenticación

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| POST | `/api/register/` | `AllowAny` | Registro de nuevo usuario |
| POST | `/api/login/` | `AllowAny` | Inicio de sesión (retorna JWT) |
| POST | `/api/auth/google/` | `AllowAny` | Inicio de sesión con Google OAuth |
| GET | `/api/me/` | `IsAuthenticated` | Datos del usuario actual |

## Certificados — `/api/certificates/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/certificates/` | `CanManageCertificates` | Lista paginada (filtros: search, status, event) |
| POST | `/api/certificates/` | `CanManageCertificates` | Crear certificado |
| GET | `/api/certificates/{id}/` | `CanManageCertificates` | Detalle con delivery_history |
| DELETE | `/api/certificates/{id}/` | `CanManageCertificates` | Eliminar certificado |
| POST | `/api/certificates/{id}/generate/` | `CanManageCertificates` | Generar PDF |
| POST | `/api/certificates/{id}/deliver/` | `CanManageCertificates` | Entregar (email/whatsapp/link) |
| GET | `/api/certificates/{id}/history/` | `CanManageCertificates` | Historial de entregas |
| POST | `/api/certificates/{id}/retry/` | `CanManageCertificates` | Reintentar entrega fallida |
| GET | `/api/certificates/verify/` | `AllowAny` | Verificación pública por `?code=XXXX` |
| GET | `/api/certificates/export/` | `IsAdmin` | Exportar CSV/Excel (`?file_format=csv`) |
| POST | `/api/certificates/generate-bulk/` | `IsOperationalUser` | Generación masiva desde Excel |
| POST | `/api/certificates/preview/` | `IsOperationalUser` | Previsualizar datos del Excel |
| POST | `/api/certificates/process/` | `IsOperationalUser` | Procesar datos editados |

## Eventos — `/api/events/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/events/` | `CanManageEvents` | Lista paginada (filtros: search, status, category) |
| POST | `/api/events/` | `CanManageEvents` | Crear evento |
| GET | `/api/events/{id}/` | `CanManageEvents` | Detalle de evento |
| PATCH | `/api/events/{id}/` | `CanManageEvents` | Actualizar parcial |
| DELETE | `/api/events/{id}/` | `CanManageEvents` | Eliminar (soft delete) |
| POST | `/api/events/{id}/restore/` | `CanManageEvents` | Restaurar eliminado |
| GET | `/api/events/{id}/participants/` | `IsOperationalUser` | Participantes con estado de certificado |
| POST | `/api/events/{id}/enroll/` | `IsOperationalUser` | Inscribir participante |
| POST | `/api/events/{id}/certificates/generate/` | `IsOperationalUser` | Generar certificados del evento |
| POST | `/api/events/{id}/certificates/send/` | `IsOperationalUser` | Enviar certificados del evento |
| GET | `/api/events/{id}/deliveries/` | `IsOperationalUser` | Entregas del evento |
| GET | `/api/events/{id}/stats/` | `IsOperationalUser` | Estadísticas del evento |
| GET | `/api/events/{id}/invitations/` | `IsOperationalUser` | Invitaciones del evento |
| POST | `/api/events/{id}/invitations/send/` | `IsOperationalUser` | Enviar invitaciones (archivo o emails) |
| POST | `/api/events/{id}/invitations/send-all/` | `IsOperationalUser` | Enviar a todos los invitados pendientes |
| POST | `/api/events/{id}/finalize/` | `IsOperationalUser` | Finalizar evento (opcional: auto-generar/enviar) |

## Participantes — `/api/participants/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/participants/` | `CanManageStudents` | Lista paginada (filtros: search, is_active) |
| POST | `/api/participants/` | `CanManageStudents` | Crear participante |
| GET | `/api/participants/{id}/` | `CanManageStudents` | Detalle |
| PATCH | `/api/participants/{id}/` | `CanManageStudents` | Actualizar |
| DELETE | `/api/participants/{id}/` | `CanManageStudents` | Soft delete |
| POST | `/api/participants/{id}/restore/` | `CanManageStudents` | Restaurar |
| POST | `/api/participants/import_participants/` | `CanManageStudents` | Importar desde Excel |

## Instructores — `/api/instructors/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/instructors/` | `CanManageInstructors` | Lista |
| POST | `/api/instructors/` | `CanManageInstructors` | Crear (multipart) |
| GET | `/api/instructors/{id}/` | `CanManageInstructors` | Detalle |
| PATCH | `/api/instructors/{id}/` | `CanManageInstructors` | Actualizar (multipart) |
| DELETE | `/api/instructors/{id}/` | `CanManageInstructors` | Eliminar |

## Plantillas — `/api/templates/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/templates/` | `CanManageTemplates` | Lista |
| POST | `/api/templates/` | `CanManageTemplates` | Crear |
| GET | `/api/templates/{id}/` | `CanManageTemplates` | Detalle |
| PUT | `/api/templates/{id}/` | `CanManageTemplates` | Actualizar completa |
| PATCH | `/api/templates/{id}/` | `CanManageTemplates` | Actualizar parcial |
| DELETE | `/api/templates/{id}/` | `CanManageTemplates` | Eliminar |
| POST | `/api/templates/{id}/upload-image/` | `CanManageTemplates` | Subir imagen de fondo |
| POST | `/api/templates/{id}/upload-signature/` | `CanManageTemplates` | Subir firma digital |
| GET | `/api/templates/{id}/preview/` | `CanManageTemplates` | Vista previa |
| GET | `/api/templates/by-category/` | `CanManageTemplates` | Filtrar por categoría |

## Inscripciones — `/api/enrollments/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/enrollments/` | `IsOperationalUser` | Lista de inscripciones |

## Invitaciones — Públicas

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/invitations/{token}/` | `AllowAny` | Detalle público de invitación |
| POST | `/api/invitations/{token}/accept/` | `AllowAny` | Aceptar invitación |
| POST | `/api/invitations/{token}/register/` | `AllowAny` | Registrarse y aceptar invitación |

## Entregas — `/api/deliveries/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/deliveries/` | `IsOperationalUser` | Lista de entregas (filtro: certificate_id) |

## Auditoría — `/api/audit/`

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/audit/` | `IsAdmin` | Registros de auditoría (filtros: action, user_id) |

## Documentación API

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/schema/` | `AllowAny` | OpenAPI Schema |
| GET | `/api/docs/` | `AllowAny` | Swagger UI |
