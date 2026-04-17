import csv
from django.http import StreamingHttpResponse
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AuditLog
from .serializers import AuditLogSerializer
from common.pagination import PayLeafPagination

class AuditLogPagination(PayLeafPagination):
    ordering = '-ts'

class AuditLogList(generics.ListAPIView):
    """GET /audit-logs — List + filter activity."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    pagination_class = AuditLogPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        actor_id = self.request.query_params.get('actor_id')
        action = self.request.query_params.get('action')
        resource = self.request.query_params.get('resource')
        from_ts = self.request.query_params.get('from')
        to_ts = self.request.query_params.get('to')
        ip = self.request.query_params.get('ip')

        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)
        if action:
            queryset = queryset.filter(action=action)
        if resource:
            queryset = queryset.filter(resource_type=resource)
        if from_ts:
            queryset = queryset.filter(ts__gte=from_ts)
        if to_ts:
            queryset = queryset.filter(ts__lte=to_ts)
        if ip:
            queryset = queryset.filter(ip=ip)
        
        return queryset

class AuditLogDetail(generics.RetrieveAPIView):
    """GET /audit-logs/{id} — Retrieve single entry."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

class AuditLogExport(APIView):
    """GET /audit-logs/export?from=...&to=... — CSV stream."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        rows = AuditLog.objects.all()
        from_ts = request.query_params.get('from')
        to_ts = request.query_params.get('to')
        if from_ts:
            rows = rows.filter(ts__gte=from_ts)
        if to_ts:
            rows = rows.filter(ts__lte=to_ts)

        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        
        def stream():
            yield writer.writerow(['id', 'ts', 'actor_id', 'actor_email', 'action', 'resource_type', 'resource_id', 'ip', 'result'])
            for row in rows.iterator():
                yield writer.writerow([
                    row.id, row.ts.isoformat(), row.actor_id, row.actor_email, 
                    row.action, row.resource_type, row.resource_id, row.ip, row.result
                ])

        response = StreamingHttpResponse(stream(), content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        return response
