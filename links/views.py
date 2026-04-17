from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import PaymentLink
from .serializers import PaymentLinkSerializer
from apikeys.permissions import RequiresScope

class PaymentLinkViewSet(viewsets.ModelViewSet):
    """Admin CRUD for Payment Links."""
    queryset = PaymentLink.objects.all()
    serializer_class = PaymentLinkSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'links:read'
        else:
            self.required_scope = 'links:write'
        return super().get_permissions()

class PaymentLinkPublicView(APIView):
    """
    Public GET /p/{slug} for checkout.
    No authentication required.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        link = get_object_or_404(PaymentLink, slug=slug, is_active=True)
        return Response({
            "id": link.id,
            "title": link.title,
            "description": link.description,
            "amount": link.amount,
            "currency": link.currency,
        })
