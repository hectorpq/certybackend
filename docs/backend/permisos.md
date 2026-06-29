# Permisos y Control de Acceso — `api/permissions.py`

## Roles del Sistema

| Rol | Helper | Descripción |
|-----|--------|-------------|
| `admin` | `is_admin(request)` | Acceso total, auditoría, gestión de usuarios |
| `coordinador` | `is_coordinator(request)` | Operaciones del día a día |
| `participante` | no tiene helper propio | Solo lectura de sus propios datos |

`is_operational_user(request)` — Retorna `True` para admin o coordinador.

## Clases de Permiso

| Clase | Efecto |
|-------|--------|
| `IsAdmin` | Solo usuarios con rol `admin` |
| `IsCoordinator` | Solo usuarios con rol `coordinador` |
| `IsOperationalUser` | Admin o coordinador |
| `IsAdminOrReadOnly` | Admin = acceso total; resto solo GET/HEAD/OPTIONS |
| `CanManageUsers` | Admin = CRUD; resto solo lectura |
| `CanManageCertificates` | Admin = CRUD + generar; resto solo lectura |
| `CanManageEvents` | Admin = CRUD; resto solo lectura |
| `CanManageStudents` | Admin = CRUD; resto solo lectura |
| `CanManageInstructors` | Admin = CRUD; resto solo lectura |
| `CanManageTemplates` | Admin = CRUD; resto solo lectura |

## Permisos en Línea (en `views.py`)

Además de las clases anteriores, existen dos permisos definidos directamente en `api/views.py`:

- `IsAdminUserOrReadOnly` — Similar a `IsAdminOrReadOnly` pero verifica `is_staff`
- `IsCertificateOwnerOrAdmin` — Permite acceso si el usuario es el creador del certificado o es admin

## Uso

```python
class EventsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOperationalUser]
```
