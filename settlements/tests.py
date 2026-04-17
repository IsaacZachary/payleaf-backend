import pytest
from rest_framework import status
from django.urls import reverse
from .models import Settlement

pytestmark = pytest.mark.django_db

def test_settlements_read_only(authenticated_client):
    client, user = authenticated_client
    Settlement.objects.create(
        amount=10000, 
        currency='USD', 
        processor_settlement_id='set_123',
        status='paid'
    )
    url = reverse('settlements:settlement-list')
    
    # List access
    resp = client.get(url)
    assert resp.status_code == 200
    assert len(resp.data['data']) == 1
    
    # Modification attempt (POST)
    resp = client.post(url, {"amount": 500})
    assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    # Modification attempt (DELETE)
    detail_url = reverse('settlements:settlement-detail', kwargs={'pk': Settlement.objects.first().pk})
    resp = client.delete(detail_url)
    assert resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
