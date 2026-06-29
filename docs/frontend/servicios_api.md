# Servicios API — `src/services/`

Capa de abstracción sobre Axios para comunicación con el backend. Todos los servicios importan `api` desde `api.ts` que maneja automáticamente los tokens JWT.

## `api.ts` — Cliente Axios

Configuración principal del cliente HTTP:

- **Base URL:** `/api` (proxy Vite en desarrollo)
- **Interceptor request:** Adjunta `Authorization: Bearer {token}` automáticamente
- **Interceptor response:** Refresca token automáticamente en 401, redirige a `/login` si falla
- **FormData:** Elimina `Content-Type` para que el navegador lo maneje

## `certificateService.ts`

| Método | Endpoint | Uso |
|--------|----------|-----|
| `getAll(params)` | `GET /api/certificates/` | Lista paginada |
| `getById(id)` | `GET /api/certificates/{id}/` | Detalle |
| `create(data)` | `POST /api/certificates/` | Crear |
| `delete(id)` | `DELETE /api/certificates/{id}/` | Eliminar |
| `generate(id, template_id?)` | `POST /api/certificates/{id}/generate/` | Generar PDF |
| `deliver(id, method, recipient?)` | `POST /api/certificates/{id}/deliver/` | Entregar |
| `getHistory(id)` | `GET /api/certificates/{id}/history/` | Historial |
| `verify(code)` | `GET /api/certificates/verify/` | Verificación pública |
| `previewExcel(file)` | `POST /api/certificates/preview/` | Previsualizar Excel |
| `generateBulk(file, dry_run?)` | `POST /api/certificates/generate-bulk/` | Bulk simple |
| `generateBulkFull(params)` | `POST /api/certificates/generate-bulk/` | Bulk completo (multipart) |
| `processEdited(data)` | `POST /api/certificates/process/` | Procesar datos editados |

## `eventService.ts`

| Método | Endpoint | Uso |
|--------|----------|-----|
| `getAll(params)` | `GET /api/events/` | Lista paginada |
| `getById(id)` | `GET /api/events/{id}/` | Detalle |
| `create(data)` | `POST /api/events/` | Crear |
| `update(id, data)` | `PATCH /api/events/{id}/` | Actualizar |
| `delete(id)` | `DELETE /api/events/{id}/` | Eliminar |
| `restore(id)` | `POST /api/events/{id}/restore/` | Restaurar |
| `getParticipants(id)` | `GET /api/events/{id}/participants/` | Participantes |
| `generateCertificates(id, ids?)` | `POST /api/events/{id}/certificates/generate/` | Generar lote |

## `participantService.ts`

| Método | Endpoint | Uso |
|--------|----------|-----|
| `getAll(params)` | `GET /api/participants/` | Lista paginada |
| `getById(id)` | `GET /api/participants/{id}/` | Detalle |
| `create(data)` | `POST /api/participants/` | Crear |
| `update(id, data)` | `PATCH /api/participants/{id}/` | Actualizar |
| `delete(id)` | `DELETE /api/participants/{id}/` | Eliminar |
| `restore(id)` | `POST /api/participants/{id}/restore/` | Restaurar |
| `importExcel(file)` | `POST /api/participants/import_participants/` | Importar Excel |

## `instructorService.ts`

| Método | Endpoint |
|--------|----------|
| `getAll()` | `GET /api/instructors/` |
| `getById(id)` | `GET /api/instructors/{id}/` |
| `create(data)` | `POST /api/instructors/` |
| `update(id, data)` | `PATCH /api/instructors/{id}/` |
| `delete(id)` | `DELETE /api/instructors/{id}/` |

## `authService.ts`

| Método | Endpoint | Uso |
|--------|----------|-----|
| `login(email, password)` | `POST /api/login/` | Inicio de sesión |
| `register(data)` | `POST /api/register/` | Registro |
| `googleLogin(credential)` | `POST /api/auth/google/` | Google OAuth |
| `refreshToken(refresh)` | `POST /api/token/refresh/` | Renovar token |
| `getCurrentUser()` | `GET /api/me/` | Usuario actual |
