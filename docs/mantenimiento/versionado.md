# Versionado Semántico

## Esquema

```
vMAJOR.MINOR.PATCH
```

| Componente | Cuándo incrementar | Ejemplo |
|------------|-------------------|---------|
| **MAJOR** | Cambios incompatibles en API | v2.0.0 |
| **MINOR** | Nuevas funcionalidades compatibles | v1.3.0 |
| **PATCH** | Correcciones de bugs compatibles | v1.0.1 |

## Versión Actual

**v1.0.0** — Versión inicial del sistema.

## Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| v1.0.0 | — | Versión inicial: CRUD de eventos, certificados, participantes; generación de PDFs; envío por email; autenticación JWT + Google OAuth |

## Política

- Cada release se taggea en Git: `git tag -a vX.Y.Z -m "mensaje"`
- Las ramas `release/vX.Y.Z` se crean desde `develop`
- Los hotfixes se versionan como PATCH sobre la rama `main`
