import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeAdapter:
    """
    Stripe implementation of the payment processor interface.
    """
    @staticmethod
    def create_intent(amount, currency, customer_id=None, metadata=None, capture_method='automatic'):
        params = {
            "amount": amount,
            "currency": currency.lower(),
            "metadata": metadata or {},
            "capture_method": 'automatic' if capture_method == 'automatic' else 'manual',
        }
        # In a real app, we'd map customer_id to a Stripe customer object
        intent = stripe.PaymentIntent.create(**params)
        return {
            "processor_id": intent.id,
            "client_secret": intent.client_secret,
            "status": intent.status,
        }

    @staticmethod
    def confirm(processor_id, payment_method_id):
        intent = stripe.PaymentIntent.confirm(
            processor_id,
            payment_method=payment_method_id
        )
        return {"status": intent.status}

    @staticmethod
    def capture(processor_id, amount=None):
        params = {}
        if amount:
            params["amount_to_capture"] = amount
        intent = stripe.PaymentIntent.capture(processor_id, **params)
        return {"status": intent.status}

    @staticmethod
    def cancel(processor_id):
        intent = stripe.PaymentIntent.cancel(processor_id)
        return {"status": intent.status}

    @staticmethod
    def create_refund(processor_id, amount=None, metadata=None):
        params = {"payment_intent": processor_id}
        if amount:
            params["amount"] = amount
        if metadata:
            params["metadata"] = metadata
            
        refund = stripe.Refund.create(**params)
        return {
            "processor_id": refund.id,
            "status": refund.status,
        }
