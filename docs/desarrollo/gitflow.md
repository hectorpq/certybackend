# GitFlow

## Estrategia de Ramas

```
main
  └── develop
        ├── feature/nueva-funcionalidad
        ├── fix/arreglo-error
        ├── release/v1.2.0
        └── hotfix/parche-critico
```

## Ramas Principales

| Rama | Propósito | Origen | Destino |
|------|-----------|--------|---------|
| `main` | Código en producción | — | — |
| `develop` | Integración de desarrollo | `main` | `main` |

## Ramas de Soporte

| Rama | Propósito | Origen | Destino |
|------|-----------|--------|---------|
| `feature/*` | Nueva funcionalidad | `develop` | `develop` |
| `fix/*` | Corrección de errores | `develop` | `develop` |
| `release/*` | Preparación de release | `develop` | `main` + `develop` |
| `hotfix/*` | Parche urgente en producción | `main` | `main` + `develop` |

## Flujo de Trabajo

1. Crear rama `feature/nombre` desde `develop`
2. Trabajar en la rama con commits atómicos
3. Al terminar, crear Pull Request a `develop`
4. Code review + aprobación → merge
5. Para release: crear rama `release/vX.Y.Z` desde `develop`
6. Merge a `main` y taggear con versión
7. Merge también a `develop` para mantener sincronización

## Tags

```bash
git tag -a v1.0.0 -m "Release v1.0.0 - Versión inicial"
git push origin v1.0.0
```
