import pytest
import hmac
import hashlib
import json
import time
from unittest import mock
from rest_framework import status
from django.urls import reverse
from webhooks.models import Webhook, WebhookDelivery
from webhooks.tasks import deliver_webhook_task

pytestmark = pytest.mark.django_db

def test_webhook_model_secret_generation():
    wh = Webhook.objects.create(url="https://test.me")
    assert wh.secret.startswith("whsec_")
    assert len(wh.secret) > 20

def test_webhook_signature_calculation():
    """Verify that the outbound signature matches the expected HMAC-SHA256."""
    secret = "whsec_constant_secret"
    timestamp = 1600000000
    payload = {"id": "evt_1", "type": "payment.succeeded"}
    
    # Canonical JSON used in task
    body = json.dumps(payload, separators=(',', ':'))
    signed_payload = f"{timestamp}.{body}"
    
    expected_v1 = hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    wh = Webhook.objects.create(url="https://example.com/hook", secret=secret, events=["payment.succeeded"])
    
    with mock.patch('requests.post') as m_post:
        m_post.return_value.status_code = 200
        m_post.return_value.text = "OK"
        
        with mock.patch('time.time', return_value=timestamp):
            deliver_webhook_task(wh.id, "payment.succeeded", payload)
            
        # Verify the headers sent to the URL
        call_headers = m_post.call_args[1]['headers']
        expected_sig_header = f"t={timestamp},v1={expected_v1}"
        assert call_headers['PayLeaf-Signature'] == expected_sig_header
        
        # Check delivery record
        delivery = WebhookDelivery.objects.first()
        assert delivery.status == 'succeeded'
        assert delivery.status_code == 200

def test_webhook_test_ping_action(authenticated_client):
    """Verify the /test endpoint enqueues a ping event."""
    client, user = authenticated_client
    wh = Webhook.objects.create(url="https://example.com/hook", events=["ping"])
    url = reverse('webhooks:webhook-test', kwargs={'pk': wh.pk})
    
    with mock.patch('webhooks.tasks.deliver_webhook_task.delay') as m_delay:
        resp = client.post(url)
        assert resp.status_code == status.HTTP_202_ACCEPTED
        m_delay.assert_called_once()
        # Verify first arg is wh.id and second is "ping"
        assert m_delay.call_args[0][0] == wh.id
        assert m_delay.call_args[0][1] == "ping"
