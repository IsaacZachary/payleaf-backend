import hmac
import hashlib
import time
import json
import requests
from celery import shared_task
from django.utils import timezone
from .models import Webhook, WebhookDelivery

@shared_task(bind=True, max_retries=6)
def deliver_webhook_task(self, webhook_id, event_type, payload):
    """
    Delivers a webhook event with exponential backoff.
    Retries: 1m, 5m, 30m, 2h, 6h, 24h.
    """
    try:
        webhook = Webhook.objects.get(id=webhook_id)
    except Webhook.DoesNotExist:
        return

    if not webhook.is_active:
        return

    timestamp = int(time.time())
    # Canonical JSON stringify
    payload_json = json.dumps(payload, separators=(',', ':'))
    signed_payload = f"{timestamp}.{payload_json}"
    
    signature = hmac.new(
        webhook.secret.encode(),
        signed_payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'PayLeaf-Webhooks/1.0',
        'PayLeaf-Signature': f"t={timestamp},v1={signature}",
        'X-PayLeaf-Event': event_type
    }

    delivery = WebhookDelivery.objects.create(
        webhook=webhook,
        event_type=event_type,
        payload=payload,
        attempt_count=self.request.retries + 1,
        last_attempt_at=timezone.now()
    )

    try:
        response = requests.post(
            webhook.url, 
            data=payload_json, 
            headers=headers, 
            timeout=10
        )
        delivery.status_code = response.status_code
        delivery.response_body = response.text[:2000] # Cap long responses

        if 200 <= response.status_code < 300:
            delivery.status = 'succeeded'
            delivery.save()
        else:
            delivery.status = 'failed'
            delivery.save()
            # Retry logic
            _reschedule_delivery(self)
            
    except Exception as e:
        delivery.status = 'failed'
        delivery.response_body = str(e)
        delivery.save()
        _reschedule_delivery(self)

def _reschedule_delivery(task_instance):
    """Calculates backoff and retries the task."""
    backoff_schedule = [60, 300, 1800, 7200, 21600, 86400]
    retries = task_instance.request.retries
    if retries < len(backoff_schedule):
        task_instance.retry(countdown=backoff_schedule[retries])
