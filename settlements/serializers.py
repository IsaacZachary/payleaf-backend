from rest_framework import serializers
from .models import Settlement

class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = [
            'id', 'amount', 'currency', 'status', 
            'payout_date', 'processor_settlement_id', 
            'summary', 'created_at'
        ]
