# Usuarios y Roles (App `users`) y Servicios (App `procesos`)

## Modelo `User` (`users/models.py`)

Modelo de usuario personalizado que extiende `AbstractBaseUser` y `PermissionsMixin`.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `BigAutoField` (PK) | Identificador único |
| `full_name` | `CharField(100)` | Nombre completo |
| `email` | `EmailField(unique)` | Correo electrónico (username field) |
| `role` | `CharField(20)` | Rol: `admin`, `coordinador`, `participante` |
| `email_app_password` | `CharField(255)` | Contraseña de aplicación para correo (opcional) |
| `admin_mode_enabled` | `BooleanField` | Modo administrador habilitado |
| `is_active` | `BooleanField` | Usuario activo/inactivo |
| `is_staff` | `BooleanField` | Acceso al admin de Django |
| `created_at` | `DateTimeField` (auto) | Fecha de registro |
| `updated_at` | `DateTimeField` (auto) | Última actualización |

**Manager personalizado:** `UserManager` con métodos `create_user()` y `create_superuser()`.

**Autenticación:** Por email (no username). El campo `USERNAME_FIELD = "email"`.

### Roles

- **admin:** Acceso total. Puede gestionar usuarios, exportar datos, ver auditoría y restaurar registros eliminados.
- **coordinador:** Usuario operativo. Puede crear eventos, gestionar participantes, generar y enviar certificados.
- **participante:** Usuario final. Solo ve sus propios certificados y eventos donde está inscrito.

### Permisos (`api/permissions.py`)

El sistema define funciones helper para control de acceso basado en roles:

- `is_admin(request)` — `True` solo si `user.role == "admin"`
- `is_coordinator(request)` — `True` solo si `user.role == "coordinador"`
- `is_operational_user(request)` — `True` para admin o coordinador (los que pueden operar el sistema)

## Endpoints de Autenticación

- `POST /api/register/` — Registro de nuevo usuario
    - Body: `{email, full_name, password, password_confirm}`
    - No requiere autenticación previa
- `POST /api/login/` — Inicio de sesión
    - Body: `{email, password}`
    - Retorna: `{access, refresh, user}`
    - No requiere autenticación previa
- `POST /api/auth/google/` — Autenticación con Google OAuth2
    - Body: `{token: google_id_token}`
    - Crea usuario automáticamente si no existe
- `GET /api/me/` — Obtener datos del usuario autenticado
    - Requiere token JWT
    - Retorna: `{id, email, full_name, role, is_active, is_staff}`
- `POST /api/token/refresh/` — Renovar token de acceso
    - Body: `{refresh: token}`
    - Retorna nuevo `access` token

## Configuración JWT (`config/settings.py`)

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}
```

## Servicios de la App `procesos/`

### `ExcelProcessingService` (`procesos/services.py`)

Servicio para importación masiva desde Excel y generación de certificados.

**Flujo de procesamiento:**

- **Lectura y validación:** `read_and_validate_structure()` — Lee el archivo Excel usando `pandas`, valida que existan las columnas requeridas (`full_name`, `email`, `document_id`) y retorna los datos para previsualización sin crear registros.
- **Procesamiento de registros:** `process_records(records)` — Procesa una lista de registros (posiblemente editados tras previsualización). Por cada registro:
    - Crea o actualiza el `Participant` (busca por `document_id` primero, luego por `email`)
    - Obtiene el `Event` (por nombre desde el Excel o usa el evento global)
    - Crea o actualiza el `Enrollment` con asistencia marcada
    - Crea el `Certificate` en estado `pending`
    - Genera el PDF
    - Envía el certificado por correo electrónico
- **Tolerancia a fallos:** Los errores por fila se registran en `ExcelProcessingResult.errors` sin detener el procesamiento de las demás filas.

### `BulkCertificateGeneratorService` (`procesos/services.py`)

Servicio de alto nivel que coordina la importación desde Excel y la generación masiva. Utiliza `ExcelProcessingService` internamente.
