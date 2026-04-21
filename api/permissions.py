"""
Custom permission classes for role-based access control
Solo dos roles: admin y participante
"""
from rest_framework import permissions


def is_admin(request):
    """Helper to check if user is admin"""
    if not request.user or not request.user.is_authenticated:
        return False
    return request.user.role == 'admin'


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