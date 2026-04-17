from django.utils import timezone
from .models import Webhook
from .tasks import deliver_webhook_task

def dispatch_webhook(event_type, payload, mode='live'):
    """
    Finds all active webhooks subscribed to an event and enqueues delivery.
    """
    # Using JSONB __contains for efficient subscription lookup
    webhooks = Webhook.objects.filter(
        is_active=True,
        mode=mode,
        events__contains=event_type
    )
    
    for wh in webhooks:
        deliver_webhook_task.delay(wh.id, event_type, payload)

def send_ping_event(webhook_id):
    """Sends a synthetic ping event for testing."""
    payload = {
        "event": "ping",
        "timestamp": int(timezone.now().timestamp()),
        "message": "PayLeaf Webhook Test"
    }
    deliver_webhook_task.delay(webhook_id, "ping", payload)
