from rest_framework import serializers
from .models import Refund

class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'amount', 'currency', 
            'status', 'reason', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'created_at']

class RefundCreateSerializer(serializers.Serializer):
    payment_id = serializers.CharField(required=True)
    amount = serializers.IntegerField(required=False, min_value=1)
    reason = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
