# Flujo de Autenticación (Frontend)

La autenticación en el frontend se gestiona principalmente a través del hook personalizado `useAuth`.

## Hook `useAuth`

Este hook es el responsable de:
- Almacenar el estado de autenticación del usuario (si está logueado o no).
- Guardar los tokens JWT (`access` y `refresh`) en `localStorage`.
- Proporcionar funciones para `login`, `logout` y `register`.
- Exponer la información del usuario autenticado a toda la aplicación a través de un Contexto de React.

## Proceso de Login

1.  El usuario introduce su email y contraseña en la página de Login.
2.  Se llama a la función `login` del hook `useAuth`.
3.  Esta función realiza una petición `POST` al endpoint `/api/login/` del backend.
4.  Si las credenciales son correctas, el backend devuelve los tokens y los datos del usuario.
5.  El hook `useAuth` guarda los tokens en `localStorage` y actualiza su estado interno.
6.  La aplicación redirige al usuario al `/dashboard`.

## Rutas Protegidas

Se utiliza un componente `ProtectedRoute` que envuelve las rutas que requieren autenticación. Este componente comprueba el estado del hook `useAuth`. Si el usuario no está autenticado, es redirigido a la página de login.