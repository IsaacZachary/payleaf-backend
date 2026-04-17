from rest_framework import serializers
from .models import CryptoCharge

class CryptoChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCharge
        fields = [
            'id', 'amount_fiat', 'currency_fiat', 'amount_crypto', 
            'currency_crypto', 'address', 'status', 'expires_at', 
            'confirmations_required', 'confirmations_received', 
            'hosted_url', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'confirmations_received', 'created_at']

class CryptoRateSerializer(serializers.Serializer):
    currency = serializers.CharField(max_length=3, default='USD')
