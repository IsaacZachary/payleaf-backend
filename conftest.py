import pytest
from accounts.models import User, Role, UserRole


@pytest.fixture
def create_roles(db):
    """Create all standard roles."""
    roles = {}
    for name, _ in Role.ROLE_CHOICES:
        roles[name] = Role.objects.create(name=name)
    return roles


@pytest.fixture
def create_user(db):
    """Factory fixture — create a user with optional roles."""
    def _create(email='test@payleaf.app', password='TestPass123!', roles=None):
        user = User.objects.create_user(email=email, password=password)
        if roles:
            for role_name in roles:
                role, _ = Role.objects.get_or_create(name=role_name)
                UserRole.objects.create(user=user, role=role)
        return user
    return _create


@pytest.fixture
def api_client():
    """DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, create_user):
    """API client with an authenticated session."""
    user = create_user(roles=['admin'])
    api_client.force_login(user)
    return api_client, user
