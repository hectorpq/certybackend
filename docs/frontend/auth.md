# Autenticación y Sesión

## Flujo de Sesión JWT

- **Inicio de Sesión:** El usuario envía `POST /api/login/` con email y contraseña. El backend valida las credenciales y retorna un par de tokens JWT: `access` (8 horas) y `refresh` (7 días), junto con los datos del usuario (id, email, full_name, role, is_staff).
- **Google OAuth:** Alternativamente, el usuario puede iniciar sesión con Google. El frontend envía el token de identidad de Google a `POST /api/auth/google/`. Si el email no existe en el sistema, se crea un usuario automáticamente.
- **Registro:** `POST /api/register/` con email, full_name, password y password_confirm. No requiere autenticación previa.

## Almacenamiento en el Cliente

Los tokens se almacenan en `localStorage` con las claves:

- `access_token` — Token de acceso JWT
- `refresh_token` — Token de refresco JWT

## Interceptor de Axios (`services/api.ts`)

El cliente Axios configurado en `api.ts` intercepta las peticiones y respuestas:

### Request Interceptor

- Antes de cada petición, lee `access_token` de `localStorage`.
- Si existe y la URL no es `/login/` ni `/register/`, añade el header `Authorization: Bearer {token}`.
- Si el body es `FormData`, elimina el `Content-Type` para que el navegador lo establezca automáticamente con el boundary correcto.

### Response Interceptor

- Si recibe un `401 Unauthorized` y la petición no es de refresco:
    - Intenta renovar el token usando `refresh_token` via `POST /api/token/refresh/`
    - Si la renovación es exitosa, guarda el nuevo `access_token` y reintenta la petición original
    - Si la renovación falla, limpia los tokens y redirige a `/login`
- Si recibe `401` en la petición de refresco, redirige directamente a `/login`

## Hook `useAuth` (`hooks/useAuth.ts`)

**Dependencias:** `@tanstack/react-query`, `react-router-dom`, `authService`.

Estado expuesto:

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `user` | `User \| undefined` | Datos del usuario autenticado |
| `isAdmin` | `boolean` | `true` si role es `admin` o `coordinador` |
| `isAuthenticated` | `boolean` | `true` si hay token y usuario cargado |
| `isLoadingUser` | `boolean` | Cargando datos del usuario |
| `error` | `string \| null` | Mensaje de error de autenticación |
| `login` | `function` | Mutación para iniciar sesión |
| `loginWithGoogle` | `function` | Mutación para Google OAuth |
| `register` | `function` | Mutación para registro |
| `logout` | `function` | Cierra sesión y limpia estado |

**Flujo:**

- Al cargar, si hay `access_token`, ejecuta `GET /api/me/` para obtener los datos del usuario.
- Al hacer login exitoso, guarda los tokens, actualiza la caché de React Query con los datos del usuario y redirige a `/dashboard`.
- Al hacer logout, elimina tokens del localStorage, limpia toda la caché de React Query, limpia sessionStorage y redirige a `/login`.

## Protección de Rutas

En `App.tsx`:

- `ProtectedRoute` — Verifica `isAuthenticated`. Si no hay sesión, redirige a `/login`.
- `AdminRoute` — Verifica `isAdmin` (admin o coordinador). Si no, redirige a `/dashboard`.
