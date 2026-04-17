from rest_framework import viewsets, permissions
from .models import Settlement
from .serializers import SettlementSerializer
from apikeys.permissions import RequiresScope

class SettlementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view for Settlements.
    Populated by daily reconciliation jobs.
    """
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer
    permission_classes = [permissions.IsAuthenticated | RequiresScope]
    required_scope = 'settlements:read'
