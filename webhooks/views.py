from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Webhook, WebhookDelivery
from .serializers import WebhookSerializer, WebhookDeliverySerializer
from .utils import send_ping_event
from apikeys.permissions import RequiresScope

class WebhookViewSet(viewsets.ModelViewSet):
    """
    Management of outbound Webhooks.
    """
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'webhooks:read'
        else:
            self.required_scope = 'webhooks:write'
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """POST /webhooks/{id}/test — Trigger a synthetic ping event."""
        webhook = self.get_object()
        send_ping_event(webhook.id)
        return Response({"message": "Ping event enqueued."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """GET /webhooks/{id}/deliveries — List delivery logs for this webhook."""
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()
        page = self.paginate_queryset(deliveries)
        if page is not None:
            serializer = WebhookDeliverySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)
