import pytest
from unittest import mock
from rest_framework import status
from django.urls import reverse
from payments.models import PaymentIntent
from refunds.models import Refund

pytestmark = pytest.mark.django_db

def test_refund_creation(authenticated_client):
    client, user = authenticated_client
    payment = PaymentIntent.objects.create(amount=1000, processor_id='pi_123', currency='USD')
    url = reverse('refunds:refund-list')
    
    with mock.patch('payments.processors.stripe_adapter.StripeAdapter.create_refund') as m_refund:
        m_refund.return_value = {"processor_id": "re_123", "status": "succeeded"}
        
        resp = client.post(url, {
            "payment_id": payment.id,
            "amount": 500,
            "reason": "requested_by_customer"
        }, format='json')
        
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['amount'] == 500
        assert resp.data['status'] == 'succeeded'
        assert Refund.objects.filter(payment=payment).count() == 1
