from django.db import models
from common.models import PrefixedIDMixin

class Settlement(PrefixedIDMixin):
    ID_PREFIX = 'set'
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    amount = models.IntegerField() # minor units
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    processor_settlement_id = models.CharField(max_length=255, db_index=True)
    payout_date = models.DateField(null=True, blank=True)
    
    summary = models.JSONField(default=dict) # e.g. {net: ..., fees: ..., gross: ...}

    class Meta:
        db_table = 'settlements'
        ordering = ['-created_at']

    def __str__(self):
        return f"Settlement {self.id} - {self.amount} {self.currency}"
