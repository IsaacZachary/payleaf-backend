import uuid
from django.db import models

class PrefixedIDMixin(models.Model):
    id = models.CharField(primary_key=True, max_length=50, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @classmethod
    def generate_id(cls, prefix):
        # generate a unique ID with a prefix
        # We'll use a shortened UUID to keep it manageable but unique
        return f"{prefix}_{uuid.uuid4().hex[:16]}"

    def save(self, *args, **kwargs):
        if not self.id:
            # The actual prefix should be defined in the child class
            prefix = getattr(self, 'ID_PREFIX', 'pl')
            self.id = self.generate_id(prefix)
        super().save(*args, **kwargs)
