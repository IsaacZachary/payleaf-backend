import pytest
from rest_framework import status
from django.urls import reverse
from compliance.models import BusinessProfile, KycDocument

pytestmark = pytest.mark.django_db

def test_kyc_document_encryption():
    """Verify row-level encryption for S3 keys."""
    plain = "s3-secret-path/customer-123/passport.jpg"
    encrypted = KycDocument.encrypt_key(plain)
    assert encrypted != plain
    
    doc = KycDocument(file_key_encrypted=encrypted)
    assert doc.decrypt_key() == plain

def test_compliance_submit_locks_profile(authenticated_client):
    """Verify that submitting a profile locks it for further edits."""
    client, user = authenticated_client
    profile = BusinessProfile.objects.create(
        legal_name="Acme Corp", 
        registration_number="REG-123", 
        business_type="CORP", 
        website="https://acme.inc"
    )
    # Detail URL for viewsets uses pk
    url = reverse('compliance:compliance-detail', kwargs={'pk': profile.pk})
    submit_url = f"{url}/submit"
    
    # Submit profile
    resp = client.post(submit_url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['is_locked'] is True
    assert resp.data['status'] == 'under_review'
    
    # Try adding a representative after locking
    rep_url = f"{url}/representatives"
    resp = client.post(rep_url, {
        "first_name": "Jane", 
        "last_name": "Doe", 
        "dob": "1985-05-12", 
        "email": "jane@acme.inc", 
        "job_title": "Director"
    })
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "locked" in resp.data['error']

def test_kyc_document_upload(authenticated_client):
    """Verify document upload with encrypted key storage."""
    client, user = authenticated_client
    profile = BusinessProfile.objects.create(
        legal_name="Tech Solutions", 
        registration_number="TS-99", 
        website="https://tech.inc"
    )
    url = reverse('compliance:compliance-detail', kwargs={'pk': profile.pk}) + "/documents"
    
    payload = {
        "document_type": "registration_cert",
        "file_key": "vault/kyc/bus_123/cert.pdf",
        "file_sha256": "5f70b793776e6267098c3080766a506822c60c87fc3d6f7881d77a942da5a45b"
    }
    
    resp = client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_201_CREATED
    
    doc = KycDocument.objects.get(id=resp.data['id'])
    assert doc.decrypt_key() == "vault/kyc/bus_123/cert.pdf"
    assert doc.file_sha256 == payload['file_sha256']
