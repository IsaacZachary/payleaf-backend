from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BusinessProfile, Representative, KycDocument
from .serializers import BusinessProfileSerializer, RepresentativeSerializer, KycDocumentSerializer
from apikeys.permissions import RequiresScope

class ComplianceViewSet(viewsets.ModelViewSet):
    """
    Management of Business Profiles and KYC submission.
    """
    queryset = BusinessProfile.objects.all()
    serializer_class = BusinessProfileSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        # We'll use a broad 'compliance:read/write' scope as per contract
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'compliance:read'
        else:
            self.required_scope = 'compliance:write'
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """POST /compliance/{id}/submit — Lock profile and start KYC."""
        profile = self.get_object()
        if profile.is_locked:
            return Response({"error": "Profile is already locked and submitted."}, status=400)

        # 1. Lock the profile to prevent further edits
        profile.is_locked = True
        profile.status = 'under_review'
        profile.save()

        # 2. Dispatch background task for provider submission
        # from .tasks import submit_kyc_task
        # submit_kyc_task.delay(profile.id)
        
        return Response(BusinessProfileSerializer(profile).data)

    @action(detail=True, methods=['post'], url_path='representatives')
    def add_representative(self, request, pk=None):
        profile = self.get_object()
        if profile.is_locked:
            return Response({"error": "Cannot edit a locked profile."}, status=400)
            
        serializer = RepresentativeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=profile)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='documents')
    def upload_document(self, request, pk=None):
        profile = self.get_object()
        if profile.is_locked:
            return Response({"error": "Cannot edit a locked profile."}, status=400)
            
        # Implementation of secure file upload logic
        # In this POC, we accept a file_key and file_sha256
        file_key = request.data.get('file_key')
        doc_type = request.data.get('document_type')
        file_sha256 = request.data.get('file_sha256')
        
        if not file_key or not doc_type or not file_sha256:
            return Response({"error": "file_key, document_type, and file_sha256 are required."}, status=400)
            
        doc = KycDocument.objects.create(
            business=profile,
            document_type=doc_type,
            file_key_encrypted=KycDocument.encrypt_key(file_key),
            file_sha256=file_sha256
        )
        return Response(KycDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
