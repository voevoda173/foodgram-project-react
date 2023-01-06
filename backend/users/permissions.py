from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Право полного доступа только у администратора,
       для остальных - только чтение.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == "admin"
