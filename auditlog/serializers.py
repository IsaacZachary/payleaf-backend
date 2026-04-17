from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    geo = serializers.SerializerMethodField()
    resource = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'ts', 'actor', 'action', 'resource', 'ip', 
            'user_agent', 'geo', 'device', 'result', 'metadata'
        ]

    def get_actor(self, obj):
        return {
            "id": obj.actor_id,
            "email": obj.actor_email,
            "type": obj.actor_type
        }

    def get_geo(self, obj):
        return {
            "city": obj.geo_city,
            "country": obj.geo_country
        }

    def get_resource(self, obj):
        return {
            "type": obj.resource_type,
            "id": obj.resource_id
        }
