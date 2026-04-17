from rest_framework import viewsets, permissions
from .models import Customer
from .serializers import CustomerSerializer
from apikeys.permissions import RequiresScope

class CustomerViewSet(viewsets.ModelViewSet):
    """
    CRUD for Customers.
    Supports soft deletion by setting deleted_at.
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    
    # Permission: requires either session auth or API key with correct scope
    permission_classes = [permissions.IsAuthenticated | RequiresScope]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_scope = 'customers:read'
        else:
            self.required_scope = 'customers:write'
        return super().get_permissions()

    def perform_destroy(self, instance):
        # Implement soft delete
        instance.soft_delete()
