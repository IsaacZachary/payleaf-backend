import nanoid
from django.db import models
from common.models import PrefixedIDMixin

def generate_link_slug():
    # 10 character short slug as per Step 8
    return nanoid.generate(size=10)

class PaymentLink(PrefixedIDMixin):
    ID_PREFIX = 'plink'
    
    slug = models.CharField(max_length=10, unique=True, default=generate_link_slug)
    amount = models.PositiveIntegerField() # minor units
    currency = models.CharField(max_length=3, default='USD')
    
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'payment_links'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.slug})"
