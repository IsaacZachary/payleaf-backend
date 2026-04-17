import pytest
from rest_framework import status
from django.urls import reverse
from .models import AuditLog

pytestmark = pytest.mark.django_db

def test_hash_chain_integrity(create_user):
    # Create first entry
    log1 = AuditLog.objects.create(action="test.action1", actor_id="user1")
    assert log1.prev_hash == "0" * 64
    assert log1.row_hash is not None
    
    # Create second entry
    log2 = AuditLog.objects.create(action="test.action2", actor_id="user2")
    assert log2.prev_hash == log1.row_hash
    assert log2.row_hash is not None

def test_middleware_logs_mutating_request(api_client, create_user):
    user = create_user(roles=['admin'])
    api_client.force_login(user)
    
    # Trigger a mutating request (change password)
    url = reverse('accounts:change-password')
    api_client.post(url, {
        'old_password': 'TestPass123!',
        'new_password': 'NewPass456!',
    }, format='json')
    
    # Verify audit log exists
    log = AuditLog.objects.filter(actor_id=user.prefixed_id, action="accounts:change-password").first()
    assert log is not None
    assert log.actor_type == "user"
    assert log.result == "success"

def test_audit_log_list_and_filter(authenticated_client):
    client, user = authenticated_client
    # Create some logs
    AuditLog.objects.create(action="test.a", actor_id="u1", ip="1.1.1.1")
    AuditLog.objects.create(action="test.b", actor_id="u2", ip="2.2.2.2")
    
    url = reverse('auditlog:audit-log-list')
    resp = client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    # DRF might wrap in 'results' if using pagination by default, or just 'data'
    data = resp.data.get('data', resp.data)
    assert len(data) >= 2
    
    # Filter by IP
    resp = client.get(url + "?ip=1.1.1.1")
    data = resp.data.get('data', resp.data)
    assert len(data) == 1
    assert data[0]['ip'] == "1.1.1.1"

def test_audit_log_export(authenticated_client):
    client, user = authenticated_client
    AuditLog.objects.create(action="export.test", actor_id="u1")
    
    url = reverse('auditlog:audit-log-export')
    resp = client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp['Content-Type'] == "text/csv"
    
    content = b"".join(resp.streaming_content).decode()
    assert "export.test" in content
    assert "actor_id" in content # Header
