from rest_framework import serializers
from .models import BusinessProfile, Representative, KycDocument

class RepresentativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Representative
        fields = ['id', 'first_name', 'last_name', 'dob', 'email', 'job_title']

class KycDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KycDocument
        fields = ['id', 'document_type', 'status', 'file_sha256']
        read_only_fields = ['id', 'status', 'file_sha256']

class BusinessProfileSerializer(serializers.ModelSerializer):
    representatives = RepresentativeSerializer(many=True, read_only=True)
    documents = KycDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'legal_name', 'registration_number', 'tax_id', 
            'business_type', 'website', 'status', 'is_locked', 
            'representatives', 'documents', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'is_locked', 'created_at']
