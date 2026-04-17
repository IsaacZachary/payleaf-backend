import pytest
from unittest import mock
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache
from crypto.models import CryptoCharge

pytestmark = pytest.mark.django_db

def test_crypto_rates_caching(authenticated_client):
    client, user = authenticated_client
    url = reverse('crypto:crypto-rates')
    cache.clear()
    
    # Mocking requests.get for coinbase rates
    with mock.patch('requests.get') as m_get:
        m_get.return_value.json.return_value = {
            "data": {"currency": "USD", "rates": {"BTC": "0.00001", "ETH": "0.0002"}}
        }
        m_get.return_value.status_code = 200
        m_get.return_value.raise_for_status = lambda: None
        
        # First call hits API
        resp1 = client.get(url + "?currency=USD")
        assert resp1.status_code == 200
        assert resp1.data['rates']['BTC'] == "0.00001"
        assert m_get.call_count == 1
        
        # Second call hits cache
        resp2 = client.get(url + "?currency=USD")
        assert resp2.status_code == 200
        assert m_get.call_count == 1

def test_create_crypto_charge(authenticated_client):
    client, user = authenticated_client
    url = reverse('crypto:crypto-create-charge')
    
    with mock.patch('crypto.processors.coinbase_adapter.CoinbaseAdapter.create_charge') as m_create:
        from django.utils import timezone
        import datetime
        expiry = timezone.now() + datetime.timedelta(hours=1)
        m_create.return_value = {
            "processor_id": "CB123",
            "hosted_url": "https://coinbase.com/charge/123",
            "expires_at": expiry,
            "addresses": {}
        }
        
        resp = client.post(url, {
            "amount_fiat": "50.00",
            "currency_fiat": "USD"
        }, format='json')
        
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['hosted_url'] == "https://coinbase.com/charge/123"
        assert CryptoCharge.objects.filter(processor_id="CB123").exists()

def test_poll_task_updates_status():
    from crypto.tasks import poll_pending_crypto_charges
    from django.utils import timezone
    import datetime
    
    charge = CryptoCharge.objects.create(
        amount_fiat=10, 
        currency_fiat='USD',
        amount_crypto=0.1,
        currency_crypto='BTC',
        address='abc',
        expires_at=timezone.now() + datetime.timedelta(hours=1),
        processor_id='CB_POLL',
        status='pending'
    )
    
    with mock.patch('crypto.processors.coinbase_adapter.CoinbaseAdapter.get_status') as m_status:
        m_status.return_value = ('completed', {})
        
        poll_pending_crypto_charges()
        
        charge.refresh_from_db()
        assert charge.status == 'confirmed'
