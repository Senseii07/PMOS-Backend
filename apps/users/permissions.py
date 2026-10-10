"""
Permissions shared across apps.
"""
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to users with role=admin."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner or admin can access."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "admin":
            return True
        # obj must have a `user` FK or be the user itself
        owner = getattr(obj, "user", obj)
        return owner == request.user
