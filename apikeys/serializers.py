from rest_framework import serializers
from .models import ApiKey

class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ['id', 'name', 'prefix', 'scopes', 'is_active', 'mode', 'created_at']
        read_only_fields = ['id', 'prefix', 'created_at']

class ApiKeyCreateResponseSerializer(serializers.ModelSerializer):
    secret = serializers.CharField(read_only=True)
    
    class Meta:
        model = ApiKey
        fields = ['id', 'name', 'secret', 'prefix', 'scopes', 'is_active', 'mode', 'created_at']
        read_only_fields = fields
