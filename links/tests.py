import pytest
from rest_framework import status
from django.urls import reverse
from .models import PaymentLink

pytestmark = pytest.mark.django_db

def test_payment_link_admin_crud(authenticated_client):
    client, user = authenticated_client
    url = reverse('links:link-list')
    
    # Create
    resp = client.post(url, {
        "title": "Donation",
        "amount": 1000,
        "currency": "USD"
    }, format='json')
    assert resp.status_code == status.HTTP_201_CREATED
    assert len(resp.data['slug']) == 10

def test_payment_link_public_access(api_client):
    link = PaymentLink.objects.create(title="Coffee", amount=500, currency="USD")
    url = reverse('links:public-checkout', kwargs={'slug': link.slug})
    
    # Ensure no credentials
    api_client.credentials()
    resp = api_client.get(url)
    
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['title'] == "Coffee"
    assert resp.data['amount'] == 500
    # Sensitive metadata or slugs shouldn't be here if not strictly needed
    # but the config is returned.
