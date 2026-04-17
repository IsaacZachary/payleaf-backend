from rest_framework import permissions

class RequiresScope(permissions.BasePermission):
    """
    Enforces scope-based access for API keys.
    Works for both API key auth (request.auth) and session auth (request.user).
    Session users (admins, etc.) are granted access if they are authenticated.
    """
    def __init__(self, required_scope=None):
        self.required_scope = required_scope

    def has_permission(self, request, view):
        # If authenticated via session (user is present), allow all (admin-like)
        if request.user and request.user.is_authenticated:
            # Note: Role checks like 'HasRole' should be used in conjunction if needed.
            return True
            
        # Check API key scopes
        api_key = request.auth
        if api_key and hasattr(api_key, 'scopes'):
            required = self.required_scope or getattr(view, 'required_scope', None)
            if not required:
                return True
            return required in api_key.scopes

        return False

def Scoped(scope):
    """Factory to create a RequiresScope instance with a specific scope."""
    class DynamicScopedPermission(RequiresScope):
        def __init__(self):
            super().__init__(required_scope=scope)
    return DynamicScopedPermission
