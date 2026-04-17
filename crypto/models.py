from django.db import models
from common.models import PrefixedIDMixin

class CryptoCharge(PrefixedIDMixin):
    ID_PREFIX = 'chg'
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]

    amount_fiat = models.DecimalField(max_digits=20, decimal_places=2)
    currency_fiat = models.CharField(max_length=3, default='USD')
    
    amount_crypto = models.DecimalField(max_digits=36, decimal_places=18)
    currency_crypto = models.CharField(max_length=10) # e.g. BTC, ETH
    
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    expires_at = models.DateTimeField()
    confirmations_required = models.IntegerField(default=2)
    confirmations_received = models.IntegerField(default=0)
    
    processor_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    hosted_url = models.URLField(null=True, blank=True)
    
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'crypto_charges'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.amount_crypto} {self.currency_crypto} ({self.status})"
