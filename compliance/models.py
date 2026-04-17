from django.db import models
from common.models import PrefixedIDMixin
from cryptography.fernet import Fernet
from django.conf import settings

class BusinessProfile(PrefixedIDMixin):
    ID_PREFIX = 'bus'
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]

    legal_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    
    business_type = models.CharField(max_length=50)
    website = models.URLField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_locked = models.BooleanField(default=False)
    
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'compliance_business_profiles'

class Representative(PrefixedIDMixin):
    ID_PREFIX = 'rep'
    
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='representatives')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    email = models.EmailField()
    job_title = models.CharField(max_length=100)

    class Meta:
        db_table = 'compliance_representatives'

class KycDocument(PrefixedIDMixin):
    ID_PREFIX = 'doc'
    
    business = models.ForeignKey(BusinessProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50) # e.g. passport, proof_of_address
    
    # Security: Store only encrypted key and high-entropy hash
    file_key_encrypted = models.TextField() # Encrypted S3/Storage key
    file_sha256 = models.CharField(max_length=64) # For integrity checks
    
    status = models.CharField(max_length=20, default='pending')

    class Meta:
        db_table = 'compliance_kyc_documents'

    @classmethod
    def _get_fernet(cls):
        import base64
        # Derive a 32-byte URL-safe base64 key from Django SECRET_KEY
        key = base64.urlsafe_b64encode(settings.SECRET_KEY[:32].encode().ljust(32, b'0'))
        return Fernet(key)

    @classmethod
    def encrypt_key(cls, plain_key):
        f = cls._get_fernet()
        return f.encrypt(plain_key.encode()).decode()

    def decrypt_key(self):
        f = self._get_fernet()
        return f.decrypt(self.file_key_encrypted.encode()).decode()
