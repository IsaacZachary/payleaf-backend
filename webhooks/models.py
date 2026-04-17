import secrets
from django.db import models
from common.models import PrefixedIDMixin

def generate_webhook_secret():
    return f"whsec_{secrets.token_hex(32)}"

class Webhook(PrefixedIDMixin):
    ID_PREFIX = 'wh'
    
    url = models.URLField(max_length=500)
    events = models.JSONField(default=list) # List of event strings, e.g. ["payment.succeeded"]
    secret = models.CharField(max_length=128, default=generate_webhook_secret)
    
    is_active = models.BooleanField(default=True)
    mode = models.CharField(max_length=10, default='live') # live | test
    
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} -> {self.url}"

class WebhookDelivery(PrefixedIDMixin):
    ID_PREFIX = 'whd'
    
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(null=True, blank=True)
    
    # Retry tracking
    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending') # pending, succeeded, failed

    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']
