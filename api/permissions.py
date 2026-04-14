"""
Custom permission classes for role-based access control
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol 'admin'
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == 'admin'
        )


class IsEditor(permissions.BasePermission):
    """
    Permite acceso a usuarios con rol 'admin' o 'editor'
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ['admin', 'editor']
        )


class IsAdminOrEditor(permissions.BasePermission):
    """
    Alias para IsEditor - permite admin y editor
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ['admin', 'editor']
        )


class IsAdminUser(permissions.BasePermission):
    """
    Permite cualquier acción si es admin
    Solo lectura para otros usuarios autenticados
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin puede hacer cualquier cosa
        if request.user.role == 'admin':
            return True
        
        # Otros solo pueden hacer operaciones seguras (GET, HEAD, OPTIONS)
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
        
        # Admin puede hacer cualquier cosa
        if request.user.role == 'admin':
            return True
        
        # Otros solo pueden ver su propia información (GET)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class CanManageCertificates(permissions.BasePermission):
    """
    Admin y Editor pueden generar certificados
    Solo lectura para otros
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y Editor pueden hacer cualquier cosa
        if request.user.role in ['admin', 'editor']:
            return True
        
        # Otros solo pueden ver (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class CanManageEvents(permissions.BasePermission):
    """
    Admin y Editor pueden crear/editar eventos
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y Editor pueden hacer POST, PUT, PATCH, DELETE
        if request.user.role in ['admin', 'editor']:
            return True
        
        # Otros solo GET
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class CanManageStudents(permissions.BasePermission):
    """
    Admin y Editor pueden gestionar estudiantes
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin y Editor pueden hacer cualquier cosa
        if request.user.role in ['admin', 'editor']:
            return True
        
        # Otros solo GET
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
