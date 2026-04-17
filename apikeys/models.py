import secrets
import hashlib
from django.db import models
from common.models import PrefixedIDMixin

class ApiKey(PrefixedIDMixin):
    ID_PREFIX = 'key'
    
    name = models.CharField(max_length=255)
    prefix = models.CharField(max_length=12, editable=False, db_index=True) # e.g. pl_live_abcd
    secret_hash = models.CharField(max_length=64, editable=False) # sha256
    scopes = models.JSONField(default=list) # e.g. ["payments:read", "payments:write"]
    is_active = models.BooleanField(default=True)
    mode = models.CharField(max_length=10, choices=[('live', 'Live'), ('test', 'Test')], default='live')

    class Meta:
        db_table = 'api_keys'
        ordering = ['-created_at']

    @classmethod
    def generate_key(cls, mode='live'):
        """
        Generates a new API key.
        Returns (full_secret, prefix, secret_hash)
        """
        secret = f"pl_{mode}_{secrets.token_urlsafe(32)}"
        prefix = secret[:12]
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        return secret, prefix, secret_hash

    def __str__(self):
        return f"{self.name} ({self.prefix}...)"
