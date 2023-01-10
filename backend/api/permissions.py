from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Право полного доступа только у администратора,
       для остальных - только чтение.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.is_admin


class IsAuthorOrStaff(permissions.BasePermission):
    """Право доступа предоставлено только автору и персоналу."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in ('GET', )
            or obj.author == request.user
            or request.user.is_admin
        )


class UserPermission(permissions.BasePermission):
    """Право доступа администратора или персонала."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
        )
