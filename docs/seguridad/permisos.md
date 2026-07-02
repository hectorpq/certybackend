# Permisos y Control de Acceso

## Roles

| Rol | Helper | Descripción |
|-----|--------|-------------|
| `admin` | `is_admin(request)` | Acceso total: auditoría, exportación, gestión de usuarios |
| `coordinador` | `is_coordinator(request)` | Operaciones del día a día: eventos, certificados, participantes |
| — | `is_operational_user(request)` | True para admin o coordinador |

## Clases de Permiso

| Clase | Admin | Coordinador | Participante |
|-------|-------|-------------|--------------|
| `IsAdmin` | ✅ CRUD | ❌ | ❌ |
| `IsOperationalUser` | ✅ CRUD | ✅ CRUD | ❌ |
| `IsAdminOrReadOnly` | ✅ CRUD | ✅ Read | ✅ Read |
| `CanManageUsers` | ✅ CRUD | ❌ | ❌ |
| `CanManageCertificates` | ✅ CRUD | ✅ CRUD | ✅ Read |
| `CanManageEvents` | ✅ CRUD | ✅ CRUD | ✅ Read |
| `CanManageStudents` | ✅ CRUD | ✅ CRUD | ✅ Read |
| `CanManageInstructors` | ✅ CRUD | ✅ CRUD | ✅ Read |
| `CanManageTemplates` | ✅ CRUD | ✅ CRUD | ✅ Read |

## Implementación

```python
# api/permissions.py
def is_admin(request):
    return request.user.role == "admin"

class IsOperationalUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("admin", "coordinador")
```

## Uso en Vistas

```python
class CertificateViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageCertificates]
```

## Permisos en Línea (en views.py)

- `IsAdminUserOrReadOnly` — Verifica `is_staff` para escritura
- `IsCertificateOwnerOrAdmin` — Permite acceso al creador del certificado o admin
