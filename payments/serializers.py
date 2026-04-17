from rest_framework import serializers
from .models import PaymentIntent

class PaymentIntentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'amount', 'currency', 'status', 
            'customer', 'client_secret', 'capture_method', 
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'client_secret', 'created_at']

class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    currency = serializers.CharField(max_length=3, default='USD')
    customer_id = serializers.CharField(required=False, allow_null=True)
    capture_method = serializers.ChoiceField(choices=['automatic', 'manual'], default='automatic')
    metadata = serializers.JSONField(required=False)

class PaymentConfirmSerializer(serializers.Serializer):
    payment_method_id = serializers.CharField(required=True)

class PaymentCaptureSerializer(serializers.Serializer):
    amount = serializers.IntegerField(required=False, min_value=1)
