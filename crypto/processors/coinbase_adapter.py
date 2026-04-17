from coinbase_commerce.client import Client
from django.conf import settings

class CoinbaseAdapter:
    """
    Adapter for Coinbase Commerce API.
    """
    def __init__(self):
        self.api_key = getattr(settings, 'COINBASE_API_KEY', '')
        # Lazy initialization of client
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = Client(api_key=self.api_key)
        return self._client

    def create_charge(self, amount, currency, metadata=None):
        """
        Creates a charge on Coinbase Commerce.
        Returns a dict with processor_id, hosted_url, and expiry.
        """
        charge_data = {
            "name": f"Payment via PayLeaf",
            "description": f"Ref: {metadata.get('reference') if metadata else 'N/A'}",
            "pricing_type": "fixed_price",
            "local_price": {
                "amount": str(amount),
                "currency": currency.upper()
            },
            "metadata": metadata or {}
        }
        
        charge = self.client.charge.create(**charge_data)
        
        return {
            "processor_id": charge.id,
            "hosted_url": charge.hosted_url,
            "expires_at": charge.expires_at,
            "addresses": getattr(charge, 'addresses', {}),
        }

    def get_status(self, processor_id):
        """
        Retrieves the latest status of a charge.
        """
        charge = self.client.charge.retrieve(processor_id)
        # Coinbase statuses: NEW, PENDING, COMPLETED, EXPIRED, UNRESOLVED, RESOLVED
        latest_status = charge.timeline[-1]['status']
        return latest_status.lower(), charge
