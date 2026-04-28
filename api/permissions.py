"""
Custom permission classes for role-based access control
Roles: admin, coordinador, participante
"""
from rest_framework import permissions

OPERATIONAL_ROLES = ('admin', 'coordinador')


def is_admin(request):
    """True only for 'admin' role (auditing, bulk actions, user management)."""
    if not request.user or not request.user.is_authenticated:
        return False
    return request.user.role == 'admin'


def is_coordinator(request):
    """True only for 'coordinador' role (day-to-day operations)."""
    if not request.user or not request.user.is_authenticated:
        return False
    return request.user.role == 'coordinador'


def is_operational_user(request):
    """True for admin OR coordinador — can register, enroll, generate, deliver."""
    if not request.user or not request.user.is_authenticated:
        return False
    return request.user.role in OPERATIONAL_ROLES


class IsAdmin(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol 'admin'
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and is_admin(request)
        )


class IsCoordinator(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol 'coordinador'
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and is_coordinator(request)
        )


class IsOperationalUser(permissions.BasePermission):
    """
    Permite acceso a admin y coordinador (operaciones del día a día)
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and is_operational_user(request)
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admin tiene acceso completo, participante solo lectura (GET, HEAD, OPTIONS)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class CanManageUsers(permissions.BasePermission):
    """
    Solo admin puede crear, actualizar o eliminar usuarios
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class CanManageCertificates(permissions.BasePermission):
    """
    Admin puede generar certificados
    Participante solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class CanManageEvents(permissions.BasePermission):
    """
    Admin puede crear/editar eventos
    Participante solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class CanManageStudents(permissions.BasePermission):
    """
    Admin puede gestionar estudiantes
    Participante solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class CanManageInstructors(permissions.BasePermission):
    """
    Admin puede gestionar instructores
    Participante solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False


class CanManageTemplates(permissions.BasePermission):
    """
    Admin puede gestionar plantillas
    Participante solo lectura
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_admin(request):
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        return False