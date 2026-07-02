# Convenciones de Commits

## Formato

```
<tipo>(<alcance>): <descripción>

[Cuerpo opcional]

[Pie opcional]
```

## Tipos

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato, espacios, estilos (sin cambio funcional) |
| `refactor` | Refactorización de código |
| `test` | Adición o modificación de pruebas |
| `chore` | Tareas de mantenimiento, dependencias, build |
| `perf` | Mejora de rendimiento |
| `ci` | Cambios en CI/CD |
| `security` | Parches de seguridad |

## Alcances

| Alcance | Área |
|---------|------|
| `api` | Endpoints REST |
| `models` | Modelos de base de datos |
| `services` | Servicios (email, WhatsApp, PDF) |
| `tasks` | Tareas Celery |
| `auth` | Autenticación y autorización |
| `front` | Frontend React |
| `docs` | Documentación MkDocs |
| `infra` | Docker, CI/CD, despliegue |
| `tests` | Pruebas |

## Ejemplos

```
feat(api): agregar endpoint de verificación de certificados

fix(services): corregir reintento en envío de WhatsApp

docs(api): documentar nuevo endpoint de participantes

test(models): agregar pruebas unitarias para modelo Event

ci(infra): actualizar pipeline de GitHub Actions
```

## Política de Ramas

- **main**: Solo merges de `release/*` o hotfixes
- **develop**: Integración de características
- **feature/***: Nuevas funcionalidades (merge a develop)
- **release/***: Preparación de release (merge a main y develop)
- **hotfix/***: Corrección urgente (merge a main y develop)
