from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
import requests
import logging

from .models import CryptoCharge
from .serializers import CryptoChargeSerializer, CryptoRateSerializer
from apikeys.permissions import RequiresScope

logger = logging.getLogger(__name__)

class CryptoViewSet(viewsets.ModelViewSet):
    queryset = CryptoCharge.objects.all()
    serializer_class = CryptoChargeSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        if self.action in ['rates']:
            # Public or internal access? 
            # Prompt says /crypto/rates?currency=USD
            # I'll allow anyone authenticated
            return [permissions.IsAuthenticated()]
        
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'crypto:read'
        else:
            self.required_scope = 'crypto:write'
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def rates(self, request):
        """GET /crypto/rates?currency=USD — Cached rates."""
        base = request.query_params.get('currency', 'USD').upper()
        cache_key = f"crypto_rates:{base}"
        rates = cache.get(cache_key)

        if not rates:
            try:
                # Using Coinbase's public exchange rates API
                resp = requests.get(f"https://api.coinbase.com/v2/exchange-rates?currency={base}", timeout=5)
                resp.raise_for_status()
                rates = resp.json()['data']['rates']
                cache.set(cache_key, rates, timeout=60) # Cached for 60s
            except Exception as e:
                logger.error(f"Failed to fetch crypto rates: {e}")
                return Response({"error": "Failed to fetch rates"}, status=503)

        return Response({"base": base, "rates": rates})

    @action(detail=False, methods=['post'], url_path='charges')
    def create_charge(self, request):
        """POST /crypto/charges — Create a new crypto charge."""
        # Using a partial serializer for initial input
        amount_fiat = request.data.get('amount_fiat')
        currency_fiat = request.data.get('currency_fiat', 'USD')
        
        if not amount_fiat:
            return Response({"error": "amount_fiat is required"}, status=400)

        from .processors.coinbase_adapter import CoinbaseAdapter
        try:
            adapter = CoinbaseAdapter()
            c_res = adapter.create_charge(
                amount=amount_fiat,
                currency=currency_fiat,
                metadata=request.data.get('metadata', {})
            )
            
            charge = CryptoCharge.objects.create(
                amount_fiat=amount_fiat,
                currency_fiat=currency_fiat,
                amount_crypto=0.0, # Fiat-priced charge
                currency_crypto='MULTI',
                address='hosted-page',
                status='pending',
                expires_at=c_res['expires_at'],
                processor_id=c_res['processor_id'],
                hosted_url=c_res['hosted_url'],
                metadata=request.data.get('metadata', {})
            )
            return Response(CryptoChargeSerializer(charge).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Crypto charge creation failed: {e}")
            return Response({"error": "Failed to create crypto charge"}, status= status.HTTP_400_BAD_DATA)
