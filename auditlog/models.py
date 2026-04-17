import hashlib
import uuid
import django.utils.timezone
from django.db import models
from common.utils import canonical_json

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ts = models.DateTimeField(default=django.utils.timezone.now, db_index=True)
    
    # Actor
    actor_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    actor_type = models.CharField(max_length=50, null=True, blank=True) # user, api_key, system
    actor_email = models.EmailField(null=True, blank=True)
    
    # Action & Resource
    action = models.CharField(max_length=100, db_index=True) # e.g. payment.refund
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Context
    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(null=True, blank=True)
    geo_city = models.CharField(max_length=100, null=True, blank=True)
    geo_country = models.CharField(max_length=100, null=True, blank=True)
    device = models.CharField(max_length=255, null=True, blank=True)
    
    result = models.CharField(max_length=20, default='success') # success | failure
    metadata = models.JSONField(default=dict)
    
    # Hash Chain
    prev_hash = models.CharField(max_length=64, null=True, blank=True)
    row_hash = models.CharField(max_length=64, unique=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-ts']

    def save(self, *args, **kwargs):
        if not self.row_hash:
            # Ensure ts is set for hashing
            if not self.ts:
                self.ts = django.utils.timezone.now()
                
            # Get previous hash
            # Using order_by('-ts', '-row_hash') for stability
            last_entry = AuditLog.objects.order_by('-ts').first()
            self.prev_hash = last_entry.row_hash if last_entry else "0" * 64
            
            # Compute row hash
            entry_dict = {
                "ts": self.ts.isoformat(),
                "actor_id": self.actor_id,
                "actor_type": self.actor_type,
                "actor_email": self.actor_email,
                "action": self.action,
                "resource_type": self.resource_type,
                "resource_id": self.resource_id,
                "ip": self.ip,
                "user_agent": self.user_agent,
                "geo_city": self.geo_city,
                "geo_country": self.geo_country,
                "device": self.device,
                "result": self.result,
                "metadata": self.metadata,
            }

            payload = f"{self.prev_hash}||{canonical_json(entry_dict)}"
            self.row_hash = hashlib.sha256(payload.encode()).hexdigest()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ts} - {self.actor_id} - {self.action}"
