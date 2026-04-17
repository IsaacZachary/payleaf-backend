from django.db import models
from django.utils import timezone
from common.models import PrefixedIDMixin

class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Customer(PrefixedIDMixin):
    ID_PREFIX = 'cus'
    
    email = models.EmailField(unique=True) # Contract: unique per merchant
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = CustomerManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.email} ({self.id})"
