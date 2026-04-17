import pytest
from rest_framework import status
from django.urls import reverse
from .models import Customer

pytestmark = pytest.mark.django_db

def test_customer_create(authenticated_client):
    client, user = authenticated_client
    url = reverse('customers:customer-list')
    resp = client.post(url, {
        "email": "cust@test.com",
        "name": "Test Customer",
    }, format='json')
    
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data['id'].startswith('cus_')
    assert resp.data['email'] == "cust@test.com"

def test_customer_soft_delete(authenticated_client):
    client, user = authenticated_client
    cust = Customer.objects.create(email="delete@test.com")
    
    url = reverse('customers:customer-detail', kwargs={'pk': cust.pk})
    resp = client.delete(url)
    assert resp.status_code == status.HTTP_204_NO_CONTENT
    
    # Default manager should exclude soft-deleted records
    assert Customer.objects.count() == 0
    # Verify record still exists in DB
    assert Customer.all_objects.filter(email="delete@test.com").exists()
    assert Customer.all_objects.get(email="delete@test.com").deleted_at is not None

def test_customer_unique_email(authenticated_client):
    client, user = authenticated_client
    Customer.objects.create(email="dup@test.com")
    
    url = reverse('customers:customer-list')
    resp = client.post(url, {"email": "dup@test.com"}, format='json')
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

def test_customer_api_key_access(api_client):
    from apikeys.models import ApiKey
    secret, prefix, secret_hash = ApiKey.generate_key()
    ApiKey.objects.create(
        name="Key", prefix=prefix, secret_hash=secret_hash, 
        scopes=["customers:read"]
    )
    
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {secret}')
    url = reverse('customers:customer-list')
    
    # GET succeeds with customers:read scope
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    
    # POST fails as customers:write scope is missing
    resp = api_client.post(url, {"email": "no@permission.com"}, format='json')
    assert resp.status_code == status.HTTP_403_FORBIDDEN
