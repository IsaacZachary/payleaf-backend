from django.db import models
from common.models import PrefixedIDMixin

class PaymentIntent(PrefixedIDMixin):
    ID_PREFIX = 'pi'
    
    STATUS_CHOICES = [
        ('requires_payment_method', 'Requires Payment Method'),
        ('requires_confirmation', 'Requires Confirmation'),
        ('requires_action', 'Requires Action'),
        ('processing', 'Processing'),
        ('requires_capture', 'Requires Capture'),
        ('succeeded', 'Succeeded'),
        ('canceled', 'Canceled'),
    ]

    amount = models.PositiveIntegerField() # in minor units (e.g. cents)
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='requires_payment_method')
    
    # Relationships
    customer = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Processor mapping
    processor_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    client_secret = models.CharField(max_length=255, null=True, blank=True)
    
    # Capture settings
    capture_method = models.CharField(max_length=20, default='automatic') # automatic | manual
    
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'payment_intents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.amount} {self.currency} ({self.status})"
