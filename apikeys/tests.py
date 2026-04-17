import pytest
import hashlib
from rest_framework import status
from django.urls import reverse
from .models import ApiKey
from .authentication import ApiKeyAuthentication

pytestmark = pytest.mark.django_db

def test_api_key_generation():
    secret, prefix, secret_hash = ApiKey.generate_key(mode='test')
    assert secret.startswith('pl_test_')
    assert prefix == secret[:12]
    assert secret_hash == hashlib.sha256(secret.encode()).hexdigest()

def test_api_key_create_endpoint(authenticated_client):
    client, user = authenticated_client
    url = reverse('apikeys:api-key-list')
    resp = client.post(url, {
        "name": "Test Key",
        "scopes": ["payments:read"],
        "mode": "test"
    }, format='json')
    
    assert resp.status_code == status.HTTP_201_CREATED
    assert "secret" in resp.data
    assert resp.data["secret"].startswith('pl_test_')
    assert resp.data["prefix"] == resp.data["secret"][:12]

def test_api_key_auth():
    secret, prefix, secret_hash = ApiKey.generate_key()
    api_key = ApiKey.objects.create(
        name="Auth Test",
        prefix=prefix,
        secret_hash=secret_hash,
        scopes=["payments:read"]
    )
    
    from rest_framework.test import APIRequestFactory
    factory = APIRequestFactory()
    request = factory.get('/')
    request.META['HTTP_AUTHORIZATION'] = f'Bearer {secret}'
    
    auth = ApiKeyAuthentication()
    user, key = auth.authenticate(request)
    
    assert user is None
    assert key.id == api_key.id

def test_scope_permission():
    secret, prefix, secret_hash = ApiKey.generate_key()
    ApiKey.objects.create(
        name="Scope Test",
        prefix=prefix,
        secret_hash=secret_hash,
        scopes=["payments:read"]
    )
    
    from .permissions import Scoped
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from rest_framework.test import APIRequestFactory
    
    class TestView(APIView):
        authentication_classes = [ApiKeyAuthentication]
        permission_classes = [Scoped("payments:write")]
        def get(self, request): return Response({"ok": True})

    view = TestView.as_view()
    factory = APIRequestFactory()
    
    # Case 1: Key missing required scope
    request = factory.get('/')
    request.META['HTTP_AUTHORIZATION'] = f'Bearer {secret}'
    resp = view(request)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    
    # Case 2: Key HAS required scope
    secret2, prefix2, secret_hash2 = ApiKey.generate_key()
    ApiKey.objects.create(name="Ok Key", prefix=prefix2, secret_hash=secret_hash2, scopes=["payments:write"])
    request2 = factory.get('/')
    request2.META['HTTP_AUTHORIZATION'] = f'Bearer {secret2}'
    resp2 = view(request2)
    assert resp2.status_code == status.HTTP_200_OK

def test_api_key_roll(authenticated_client):
    client, user = authenticated_client
    # Create a key
    secret, prefix, secret_hash = ApiKey.generate_key()
    key = ApiKey.objects.create(name="Roll Test", prefix=prefix, secret_hash=secret_hash)
    
    url = reverse('apikeys:api-key-roll', kwargs={'pk': key.pk})
    resp = client.post(url)
    
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["secret"] != secret
    assert resp.data["prefix"] != prefix
    
    # Verify DB update
    key.refresh_from_db()
    assert key.secret_hash != secret_hash
