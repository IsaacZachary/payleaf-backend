from rest_framework import serializers
from .models import PaymentLink

class PaymentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLink
        fields = [
            'id', 'slug', 'amount', 'currency', 
            'title', 'description', 'is_active', 
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']
