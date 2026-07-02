# Google OAuth2

## Flujo

1. El frontend carga la librería Google Identity Services
2. El usuario hace clic en "Iniciar sesión con Google"
3. Google muestra el selector de cuentas
4. El usuario selecciona su cuenta y autoriza
5. Google retorna un credential token (JWT) al frontend
6. El frontend envía el token a `POST /api/auth/google/`
7. El backend valida el token con `google.oauth2.id_token.verify_oauth2_token()`
8. Busca un usuario con el email del token
9. Si existe, inicia sesión; si no existe, crea un usuario nuevo
10. Retorna JWT como en el login normal

## Configuración

```python
# settings.py
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
```

## Endpoint

- `POST /api/auth/google/`
- Body: `{ "credential": "token_de_google" }`
- Response: `{ access, refresh, user }`

## Seguridad

- El token de Google se valida criptográficamente en el servidor
- El `GOOGLE_CLIENT_ID` se almacena como variable de entorno
- Los usuarios creados via Google OAuth tienen `role="participante"` por defecto
