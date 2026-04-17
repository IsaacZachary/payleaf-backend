from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ApiKey
from .serializers import ApiKeySerializer, ApiKeyCreateResponseSerializer

class ApiKeyViewSet(viewsets.ModelViewSet):
    """
    Manage API keys.
    Only session-authenticated users (admins/developers) can manage these.
    """
    queryset = ApiKey.objects.all()
    serializer_class = ApiKeySerializer
    permission_classes = [permissions.IsAuthenticated] # Role check could be added here

    def perform_create(self, serializer):
        # Generate the secret hash before saving
        mode = self.request.data.get('mode', 'live')
        secret, prefix, secret_hash = ApiKey.generate_key(mode=mode)
        key = serializer.save(prefix=prefix, secret_hash=secret_hash)
        # Store secret temporarily to return it in the response
        key.generated_secret = secret

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return the one-time secret
        instance = serializer.instance
        response_serializer = ApiKeyCreateResponseSerializer(instance)
        data = response_serializer.data
        data['secret'] = instance.generated_secret
        
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def roll(self, request, pk=None):
        """Regenerate the secret for this API key."""
        key = self.get_object()
        secret, prefix, secret_hash = ApiKey.generate_key(mode=key.mode)
        
        key.prefix = prefix
        key.secret_hash = secret_hash
        key.save()
        
        response_serializer = ApiKeyCreateResponseSerializer(key)
        data = response_serializer.data
        data['secret'] = secret
        
        return Response(data, status=status.HTTP_200_OK)
