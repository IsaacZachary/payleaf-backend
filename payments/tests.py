import pytest
from unittest import mock
from rest_framework import status
from django.urls import reverse
from payments.models import PaymentIntent

pytestmark = pytest.mark.django_db

@pytest.fixture
def mock_stripe():
    with mock.patch('stripe.PaymentIntent.create') as m_create, \
         mock.patch('stripe.PaymentIntent.confirm') as m_confirm, \
         mock.patch('stripe.PaymentIntent.capture') as m_capture, \
         mock.patch('stripe.PaymentIntent.cancel') as m_cancel:
        
        m_create.return_value = mock.Mock(id='pi_stripe_123', client_secret='secret_123', status='requires_payment_method')
        m_confirm.return_value = mock.Mock(status='succeeded')
        m_capture.return_value = mock.Mock(status='succeeded')
        m_cancel.return_value = mock.Mock(status='canceled')
        yield {
            'create': m_create,
            'confirm': m_confirm,
            'capture': m_capture,
            'cancel': m_cancel
        }

def test_create_payment_intent(authenticated_client, mock_stripe):
    client, user = authenticated_client
    url = reverse('payments:payment-create-intent')
    
    resp = client.post(url, {
        "amount": 1000,
        "currency": "USD",
    }, format='json')
    
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.data['id'].startswith('pi_')
    assert resp.data['status'] == 'requires_payment_method'
    assert resp.data['client_secret'] == 'secret_123'
    
    mock_stripe['create'].assert_called_once()

def test_confirm_payment(authenticated_client, mock_stripe):
    client, user = authenticated_client
    intent = PaymentIntent.objects.create(amount=1000, processor_id='pi_stripe_123')
    
    url = reverse('payments:payment-confirm', kwargs={'pk': intent.pk})
    resp = client.post(url, {"payment_method_id": "pm_123"}, format='json')
    
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['status'] == 'succeeded'
    mock_stripe['confirm'].assert_called_once_with('pi_stripe_123', payment_method='pm_123')

def get_json(resp):
    if hasattr(resp, 'data'):
        return resp.data
    import json
    return json.loads(resp.content)

def test_idempotency_replay(authenticated_client, mock_stripe):
    client, user = authenticated_client
    url = reverse('payments:payment-create-intent')
    # Using DRF Test Client which uses META for headers
    headers = {'HTTP_IDEMPOTENCY_KEY': 'unique-key-1'}
    
    # First request
    resp1 = client.post(url, {"amount": 2000, "currency": "USD"}, format='json', **headers)
    assert resp1.status_code == status.HTTP_201_CREATED
    
    # Second request (replay)
    resp2 = client.post(url, {"amount": 2000, "currency": "USD"}, format='json', **headers)
    assert resp2.status_code == status.HTTP_201_CREATED
    assert resp2.has_header('X-Idempotency-Replay')
    
    data1 = get_json(resp1)
    data2 = get_json(resp2)
    assert data1['id'] == data2['id']
    
    # Stripe should have been called only once
    assert mock_stripe['create'].call_count == 1

def test_idempotency_mismatch(authenticated_client, mock_stripe):
    client, user = authenticated_client
    url = reverse('payments:payment-create-intent')
    headers = {'HTTP_IDEMPOTENCY_KEY': 'unique-key-2'}
    
    client.post(url, {"amount": 1000, "currency": "USD"}, format='json', **headers)
    
    # Replay with DIFFERENT body
    resp = client.post(url, {"amount": 5000, "currency": "USD"}, format='json', **headers)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = get_json(resp)
    assert data['error']['code'] == 'idempotency_error'
