# Módulo: Usuarios y Roles

Este módulo gestiona las cuentas de usuario del sistema, la autenticación y los niveles de permiso.

## Modelo de Datos: `User` (Custom)

El sistema utiliza un modelo de usuario personalizado que hereda de `AbstractUser`.

- **`email`**: Se utiliza como el `USERNAME_FIELD` para la autenticación.
- **`full_name`**: Nombre completo del usuario.
- **`role`**: Define el nivel de acceso del usuario.
  - `admin`: Acceso total al sistema.
  - `coordinador`: Puede gestionar eventos, participantes y certificados.
  - `participante`: Solo puede ver sus propios certificados y eventos.
- **`is_staff`**: Booleano que otorga acceso al panel de administración de Django.

## Endpoints de Autenticación

### `POST /api/register/`
- **Descripción**: Permite a un nuevo usuario crear una cuenta.
- **Permisos**: Público.

### `POST /api/login/`
- **Descripción**: Autentica a un usuario con `email` y `password`.
- **Respuesta Exitosa**: Retorna un par de tokens JWT (`access` y `refresh`) y los datos del usuario.
- **Permisos**: Público.

### `POST /api/auth/google/`
- **Descripción**: Permite la autenticación a través de Google OAuth2.
- **Funcionamiento**: Recibe un token de identidad de Google. Si el usuario no existe, lo crea automáticamente.
- **Permisos**: Público.

### `GET /api/me/`
- **Descripción**: Devuelve la información del usuario actualmente autenticado.
- **Permisos**: Autenticado.

## Permisos

El sistema utiliza un conjunto de permisos personalizados basados en el rol del usuario (`is_admin`, `is_operational_user`) para restringir el acceso a ciertas operaciones críticas como la creación o eliminación de registros.