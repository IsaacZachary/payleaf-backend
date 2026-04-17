from celery import shared_task
from django.utils import timezone
from .models import CryptoCharge
from .processors.coinbase_adapter import CoinbaseAdapter
import logging

logger = logging.getLogger(__name__)

@shared_task(name="crypto.poll_pending_charges")
def poll_pending_crypto_charges():
    """
    Celery beat task to poll pending charges from Coinbase.
    Runs every 30-60s.
    """
    pending = CryptoCharge.objects.filter(status='pending')
    adapter = CoinbaseAdapter()
    
    for charge in pending:
        # Check if already expired in our DB
        if charge.expires_at < timezone.now():
            charge.status = 'expired'
            charge.save()
            continue

        try:
            cb_status, raw_data = adapter.get_status(charge.processor_id)
            
            # Map Coinbase status to our status
            # CB: new, pending, completed, expired, unresolved, resolved
            status_map = {
                'completed': 'confirmed',
                'resolved': 'confirmed',
                'expired': 'expired',
                'unresolved': 'failed',
                'failed': 'failed'
            }
            
            new_status = status_map.get(cb_status, 'pending')
            
            if new_status != charge.status:
                charge.status = new_status
                # In a real app, we'd extract confirmation counts from the timeline
                if new_status == 'confirmed':
                    charge.confirmations_received = charge.confirmations_required
                charge.save()
                
                if new_status == 'confirmed':
                    logger.info(f"Crypto charge {charge.id} confirmed.")
                    # TODO: Trigger webhook crypto.charge.confirmed
        except Exception as e:
            logger.error(f"Failed to poll charge {charge.id}: {e}")

@shared_task(name="crypto.cleanup_expired_charges")
def cleanup_expired_charges():
    """Mark old pending charges as expired."""
    CryptoCharge.objects.filter(
        status='pending', 
        expires_at__lt=timezone.now()
    ).update(status='expired')
