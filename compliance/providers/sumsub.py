import logging
from .base import BaseKycProvider

logger = logging.getLogger(__name__)

class SumsubProvider(BaseKycProvider):
    """
    Mock Sumsub implementation for PayLeaf KYC.
    """
    def submit_business_profile(self, business_profile):
        # In a real app, this would use Sumsub's production API
        logger.info(f"Submitting {business_profile.legal_name} to Sumsub.")
        return {"external_id": f"ss_{business_profile.id}", "status": "init"}

    def verify_webhook_signature(self, payload, signature):
        # Signature validation logic
        return True

    def handle_callback(self, data):
        # Map Sumsub statuses to internal state
        external_id = data.get('external_id')
        status = data.get('review_status') # init, pending, completed
        return external_id, status
