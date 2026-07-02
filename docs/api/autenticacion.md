# Autenticación

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/register/` | Registro de nuevo usuario |
| POST | `/api/login/` | Inicio de sesión |
| POST | `/api/auth/google/` | Google OAuth2 |
| POST | `/api/token/refresh/` | Renovar token de acceso |
| GET | `/api/me/` | Datos del usuario autenticado |

## Flujo JWT

1. El usuario envía credenciales a `POST /api/login/`
2. El backend valida y retorna `{ access, refresh, user }`
3. El frontend guarda ambos tokens en `localStorage`
4. Cada petición subsiguiente incluye `Authorization: Bearer {access}`
5. Cuando el access token expira (8h), el frontend usa el refresh token (7d) para obtener uno nuevo
6. Si el refresh falla, redirige a `/login`

## Google OAuth2

1. El frontend obtiene el credential token de Google Identity Services
2. Envía a `POST /api/auth/google/` con el token
3. El backend valida el token con `GoogleClientId`, busca o crea el usuario
4. Retorna JWT como en el login normal

## Registro

- `POST /api/register/` con `{ email, full_name, password, password_confirm }`
- Valida que las contraseñas coincidan (mínimo 8 caracteres)
- Crea usuario con `role="participante"` por defecto

## Seguridad de Tokens

| Parámetro | Valor |
|-----------|-------|
| Access token expiración | 8 horas |
| Refresh token expiración | 7 días |
| Refresh rotation | Habilitado |
| Algoritmo | HS256 |
| Almacenamiento | localStorage (frontend) |
