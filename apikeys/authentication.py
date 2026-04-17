import hashlib
from rest_framework import authentication, exceptions
from .models import ApiKey

class ApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        secret = auth_header.split(' ')[1]
        if not secret.startswith('pl_'):
            return None # Not our key format

        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        
        try:
            api_key = ApiKey.objects.get(secret_hash=secret_hash, is_active=True)
        except ApiKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or inactive API key.')

        # DRF expects returning (user, auth).
        # For API keys, we don't have a real Django user object, so we set it to None.
        # Custom permissions will check request.auth (the api_key)
        return (None, api_key)
