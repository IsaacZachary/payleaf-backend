"""
has_role() helper and HasRole DRF permission class.
"""
from rest_framework.permissions import BasePermission


def has_role(user, role_name):
    """
    Check whether a user has a given role.
    Works for both a single role string and a list of role names.
    """
    if not user or not user.is_authenticated:
        return False
    if isinstance(role_name, (list, tuple)):
        return user.user_roles.filter(role__name__in=role_name).exists()
    return user.user_roles.filter(role__name=role_name).exists()


class HasRole(BasePermission):
    """
    DRF permission class — pass required roles at class level or via
    ``self.required_roles`` on the view.

    Usage on a view:
        permission_classes = [IsAuthenticated, HasRole]
        required_roles = ['admin', 'finance']
    """

    def has_permission(self, request, view):
        required = getattr(view, 'required_roles', None)
        if not required:
            return True  # no role restriction
        return has_role(request.user, required)
