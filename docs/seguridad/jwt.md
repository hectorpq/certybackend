# JWT (JSON Web Tokens)

## Configuración

En `config/settings.py`:

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}
```

## Flujo

```
Cliente                  Servidor
  │                        │
  │── POST /api/login/ ──→│ Validar credenciales
  │←── { access, refresh, user } ──│
  │                        │
  │── GET /api/me/ ──────→│ Verificar Bearer token
  │   Authorization:       │ Extraer user del token
  │   Bearer <access>      │
  │←── { user } ──────────│
  │                        │
  │ (access expira 8h)    │
  │                        │
  │── POST /api/token/refresh/ ──→│ Validar refresh token
  │   { refresh: <token> } │ Rotar refresh
  │←── { access, refresh }─│
```

## Seguridad

- **Algoritmo:** HS256
- **Access token:** 8 horas (corto para minimizar impacto si se filtra)
- **Refresh token:** 7 días
- **Refresh rotation:** Cada vez que se usa un refresh token, se emite uno nuevo (el anterior deja de ser válido)
- **Almacenamiento en cliente:** `localStorage` (no HttpOnly; en producción considerar cookies con HttpOnly + Secure)

## Endpoints

| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/token/refresh/` | Refrescar access token |
| POST | `/api/token/verify/` | Verificar validez de token |
