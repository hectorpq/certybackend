# Hooks de React Query — `src/hooks/`

## `useAuth`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useAuth()` | hook | Estado de autenticación: `user`, `isAdmin`, `isAuthenticated`, `isLoadingUser`, `error`, `login`, `loginWithGoogle`, `register`, `logout` |

Detalles en [Autenticación](auth.md).

## `useCertificates`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useCertificates(filters)` | query | Lista paginada de certificados |
| `useCertificate(id)` | query | Detalle de certificado |
| `usePreviewExcel()` | mutation | Previsualizar archivo Excel |
| `useGenerateBulkFull()` | mutation | Generación masiva completa |

Detalles en [Dashboard](dashboard.md).

## `useEvents`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useEvents(filters)` | query | Lista paginada de eventos |
| `useEvent(id)` | query | Detalle de evento |
| `useCreateEvent()` | mutation | Crear evento |
| `useUpdateEvent()` | mutation | Actualizar evento |
| `useDeleteEvent()` | mutation | Eliminar evento (soft delete) |
| `useEventParticipants(id)` | query | Participantes de un evento |
| `useEventStats(id)` | query | Estadísticas de un evento |
| `useEventGenerateCertificates()` | mutation | Generar certificados del evento |
| `useEventDeliverCertificates()` | mutation | Enviar certificados del evento |

## `useInstructors`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useInstructors()` | query | Lista de instructores (`GET /api/instructors/`) |
| `useInstructor(id)` | query | Detalle de instructor |
| `useCreateInstructor()` | mutation | Crear instructor (FormData) |
| `useUpdateInstructor()` | mutation | Actualizar instructor (FormData) |
| `useDeleteInstructor()` | mutation | Eliminar instructor |

## `useStudents`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useStudents(filters)` | query | Lista paginada de participantes |
| `useStudent(id)` | query | Detalle de participante |
| `useCreateStudent()` | mutation | Crear participante |
| `useUpdateStudent()` | mutation | Actualizar participante |
| `useDeleteStudent()` | mutation | Eliminar participante (soft delete) |
| `useImportStudents()` | mutation | Importar desde Excel |

## `useTemplates`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useTemplates()` | query | Lista de plantillas |
| `useTemplate(id)` | query | Detalle de plantilla |

## `useTheme`

| Exportación | Tipo | Descripción |
|-------------|------|-------------|
| `useTheme()` | hook | `{ isDark: boolean, toggle: () => void }` |

Persiste la preferencia en `localStorage` con clave `theme`. Respeta `prefers-color-scheme` del sistema operativo como valor inicial. Aplica la clase `dark` al `<html>`.
