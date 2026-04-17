from django.db import models
from common.models import PrefixedIDMixin

class Refund(PrefixedIDMixin):
    ID_PREFIX = 're'
    
    payment = models.ForeignKey('payments.PaymentIntent', on_delete=models.CASCADE, related_name='refunds')
    amount = models.PositiveIntegerField() # minor units
    currency = models.CharField(max_length=3)
    
    status = models.CharField(max_length=20, default='pending') # pending, succeeded, failed
    reason = models.CharField(max_length=50, null=True, blank=True)
    
    processor_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'refunds'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.amount} {self.currency} for {self.payment_id}"
