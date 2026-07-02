# Usuarios — `users`

## Modelo `User` (Custom)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | AutoField | PK |
| `email` | EmailField (unique) | Email del usuario; usado como username |
| `full_name` | CharField(255) | Nombre completo |
| `role` | CharField(choices) | `admin`, `coordinador`, `participante` |
| `password` | CharField | Hash de la contraseña |
| `is_active` | BooleanField | Usuario activo |
| `is_staff` | BooleanField | Acceso al admin de Django |
| `created_at` | DateTimeField | Fecha de creación |
| `updated_at` | DateTimeField | Última actualización |

## Roles y Permisos

| Rol | Capabilities |
|-----|--------------|
| **admin** | CRUD de usuarios, auditoría, exportación, configuración, acceso total a todos los recursos |
| **coordinador** | CRUD de eventos, participantes, instructores, plantillas; generar y enviar certificados |
| **participante** | Solo lectura de sus certificados y eventos donde está inscrito |

Ver detalle de clases de permiso en [Permisos](../seguridad/permisos.md).

## Endpoints

| Método | URL | Permiso | Descripción |
|--------|-----|---------|-------------|
| GET | `/api/me/` | `IsAuthenticated` | Datos del usuario actual |
| POST | `/api/register/` | `AllowAny` | Registro público (rol=participante) |

La gestión de usuarios se realiza a través del admin de Django (`/admin/`), no hay endpoints públicos de CRUD de usuarios.
