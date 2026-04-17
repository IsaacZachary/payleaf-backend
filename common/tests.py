import pytest
from rest_framework import status
from django.urls import reverse
from django.core.cache import cache

pytestmark = pytest.mark.django_db

def test_request_id_middleware(authenticated_client):
    """Verify that X-Request-Id is generated and returned."""
    client, user = authenticated_client
    url = reverse('accounts:me')
    
    resp = client.get(url)
    assert 'X-Request-Id' in resp
    
    custom_rid = "req_test_12345"
    resp = client.get(url, HTTP_X_REQUEST_ID=custom_rid)
    assert resp['X-Request-Id'] == custom_rid

def test_rate_limit_headers_anonymous(api_client):
    """Verify that X-RateLimit headers are present for anonymous requests."""
    # We use a POST request on login which is a DRF view allowing anonymous
    url = reverse('accounts:login')
    cache.clear()
    
    resp = api_client.post(url)
    # Even if 400 (no data), throttles should have run
    assert 'X-RateLimit-Limit' in resp
    assert 'X-RateLimit-Remaining' in resp
    assert 'X-RateLimit-Reset' in resp

def test_exception_handler_json_format(authenticated_client):
    """Verify the standardized error format."""
    client, user = authenticated_client
    url = reverse('customers:customer-list')
    # Trigger 400 Validation Error
    resp = client.post(url, {"email": "not-an-email"}, format='json')
    
    assert resp.status_code == 400
    assert "error" in resp.data
    err = resp.data["error"]
    assert err["type"] == "invalid_request_error"
    assert "message" in err
    assert err.get("param") == "email"
    assert "request_id" in err
