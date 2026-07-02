# Política de Ramas

## Convención de Nombres

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| Feature | `feature/descripcion-corta` | `feature/carga-masiva-excel` |
| Fix | `fix/descripcion-error` | `fix/verificacion-certificado-404` |
| Release | `release/vX.Y.Z` | `release/v1.2.0` |
| Hotfix | `hotfix/descripcion` | `hotfix/envio-correo-duplicado` |
| Chore | `chore/descripcion` | `chore/actualizar-dependencias` |

## Reglas

1. **Nunca** hacer commit directo a `main` o `develop`
2. Toda integración debe pasar por Pull Request
3. Las ramas deben eliminarse después del merge
4. Los commits deben ser atómicos (un cambio lógico por commit)
5. Los mensajes de commit deben seguir el formato conventional commits

## Pull Requests

- Título descriptivo con tipo y alcance
- Descripción del cambio
- Referencia a issue si aplica
- Checklist de verificación (tests pasan, lint, etc.)
- Mínimo 1 approval antes de merge
