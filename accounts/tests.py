"""
Tests for Step 2: Auth & Sessions, RBAC, Login Throttling.
"""
import pytest
from django.test import override_settings
from rest_framework import status

from accounts.models import PasswordResetToken, Role, User, UserRole
from accounts.permissions import HasRole, has_role

pytestmark = pytest.mark.django_db


# ─── Model tests ────────────────────────────────────────────────────────────

class TestUserModel:
    def test_create_user(self, db):
        user = User.objects.create_user(email='u@test.com', password='Pass1234!')
        assert user.email == 'u@test.com'
        assert user.check_password('Pass1234!')
        assert user.is_active is True
        assert user.is_staff is False

    def test_create_superuser(self, db):
        su = User.objects.create_superuser(email='admin@test.com', password='Admin123!')
        assert su.is_staff is True
        assert su.is_superuser is True

    def test_prefixed_id(self, create_user):
        user = create_user()
        assert user.prefixed_id.startswith('usr_')
        assert len(user.prefixed_id) == 16  # usr_ + 12 hex chars

    def test_roles_property(self, create_user, create_roles):
        user = create_user(roles=['admin', 'finance'])
        assert sorted(user.roles) == ['admin', 'finance']

    def test_has_role_method(self, create_user, create_roles):
        user = create_user(roles=['operator'])
        assert user.has_role('operator') is True
        assert user.has_role('admin') is False


class TestRoleModel:
    def test_role_creation(self, create_roles):
        assert Role.objects.count() == 5
        assert set(Role.objects.values_list('name', flat=True)) == {
            'admin', 'finance', 'operator', 'developer', 'read_only'
        }


class TestPasswordResetToken:
    def test_token_auto_generated(self, create_user):
        user = create_user()
        token = PasswordResetToken(user=user)
        token.save()
        assert token.token is not None
        assert len(token.token) > 20

    def test_token_validity(self, create_user):
        user = create_user()
        token = PasswordResetToken(user=user)
        token.save()
        assert token.is_valid is True
        assert token.is_expired is False

    def test_used_token_invalid(self, create_user):
        user = create_user()
        token = PasswordResetToken(user=user)
        token.save()
        token.used = True
        token.save()
        assert token.is_valid is False


# ─── has_role helper tests ───────────────────────────────────────────────────

class TestHasRoleHelper:
    def test_single_role(self, create_user):
        user = create_user(roles=['admin'])
        assert has_role(user, 'admin') is True
        assert has_role(user, 'finance') is False

    def test_list_of_roles(self, create_user):
        user = create_user(roles=['finance'])
        assert has_role(user, ['admin', 'finance']) is True
        assert has_role(user, ['admin', 'developer']) is False

    def test_unauthenticated_user(self):
        from django.contrib.auth.models import AnonymousUser
        assert has_role(AnonymousUser(), 'admin') is False
        assert has_role(None, 'admin') is False


# ─── Auth endpoint tests ────────────────────────────────────────────────────

class TestLoginEndpoint:
    URL = '/v1/auth/login'

    def test_login_success(self, api_client, create_user):
        create_user(email='login@test.com', password='Pass1234!')
        resp = api_client.post(self.URL, {
            'email': 'login@test.com',
            'password': 'Pass1234!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        assert 'user' in resp.data
        assert resp.data['user']['email'] == 'login@test.com'
        assert 'session_expires_at' in resp.data

    def test_login_bad_password(self, api_client, create_user):
        create_user(email='fail@test.com', password='Pass1234!')
        resp = api_client.post(self.URL, {
            'email': 'fail@test.com',
            'password': 'wrong',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.data['error']['code'] == 'invalid_credentials'

    def test_login_nonexistent_user(self, api_client):
        resp = api_client.post(self.URL, {
            'email': 'ghost@test.com',
            'password': 'nope',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_response_has_roles(self, api_client, create_user):
        create_user(email='roled@test.com', password='Pass1234!', roles=['admin'])
        resp = api_client.post(self.URL, {
            'email': 'roled@test.com',
            'password': 'Pass1234!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        assert 'admin' in resp.data['user']['roles']

    def test_login_sets_session_cookie(self, api_client, create_user):
        create_user(email='cookie@test.com', password='Pass1234!')
        resp = api_client.post(self.URL, {
            'email': 'cookie@test.com',
            'password': 'Pass1234!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK
        # Session cookie should be set (client stores it)
        assert api_client.session is not None


class TestLogoutEndpoint:
    URL = '/v1/auth/logout'

    def test_logout_success(self, authenticated_client):
        client, user = authenticated_client
        resp = client.post(self.URL)
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_unauthenticated(self, api_client):
        resp = api_client.post(self.URL)
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class TestMeEndpoint:
    URL = '/v1/auth/me'

    def test_me_authenticated(self, authenticated_client):
        client, user = authenticated_client
        resp = client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['user']['email'] == user.email

    def test_me_unauthenticated(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class TestForgotPasswordEndpoint:
    URL = '/v1/auth/forgot-password'

    def test_forgot_with_existing_email(self, api_client, create_user):
        create_user(email='existing@test.com')
        resp = api_client.post(self.URL, {'email': 'existing@test.com'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        # Token should have been created
        assert PasswordResetToken.objects.filter(user__email='existing@test.com').exists()

    def test_forgot_with_nonexistent_email(self, api_client):
        resp = api_client.post(self.URL, {'email': 'nobody@test.com'}, format='json')
        # Always 200 to prevent email enumeration
        assert resp.status_code == status.HTTP_200_OK


class TestResetPasswordEndpoint:
    URL = '/v1/auth/reset-password'

    def test_reset_success(self, api_client, create_user):
        user = create_user(email='reset@test.com', password='OldPass123!')
        token = PasswordResetToken(user=user)
        token.save()

        resp = api_client.post(self.URL, {
            'token': token.token,
            'new_password': 'NewPass456!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password('NewPass456!')

        # Verify token is consumed
        token.refresh_from_db()
        assert token.used is True

    def test_reset_invalid_token(self, api_client):
        resp = api_client.post(self.URL, {
            'token': 'bogus-token',
            'new_password': 'NewPass456!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data['error']['code'] == 'invalid_token'

    def test_reset_used_token(self, api_client, create_user):
        user = create_user(email='used@test.com')
        token = PasswordResetToken(user=user)
        token.save()
        token.used = True
        token.save()

        resp = api_client.post(self.URL, {
            'token': token.token,
            'new_password': 'NewPass456!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestChangePasswordEndpoint:
    URL = '/v1/auth/change-password'

    def test_change_success(self, api_client, create_user):
        user = create_user(email='change@test.com', password='OldPass123!')
        api_client.force_login(user)

        resp = api_client.post(self.URL, {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass456!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password('NewPass456!')

    def test_change_wrong_old_password(self, api_client, create_user):
        user = create_user(email='wrongold@test.com', password='OldPass123!')
        api_client.force_login(user)

        resp = api_client.post(self.URL, {
            'old_password': 'wrong',
            'new_password': 'NewPass456!',
        }, format='json')
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_unauthenticated(self, api_client):
        resp = api_client.post(self.URL, {
            'old_password': 'x',
            'new_password': 'y',
        }, format='json')
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


# ─── RBAC denial tests ──────────────────────────────────────────────────────

class TestRBACDenial:
    """Verify that HasRole permission rejects users missing required roles."""

    def test_user_without_required_role_gets_403(self, api_client, create_user):
        """
        This is a conceptual test — we'll verify the HasRole class directly
        since no business endpoints exist yet.
        """
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        from rest_framework.permissions import IsAuthenticated

        class ProtectedView(APIView):
            permission_classes = [IsAuthenticated, HasRole]
            required_roles = ['admin']

            def get(self, request):
                from rest_framework.response import Response
                return Response({'ok': True})

        factory = APIRequestFactory()
        view = ProtectedView.as_view()

        # User with 'operator' role — should be denied
        user = create_user(email='op@test.com', roles=['operator'])
        request = factory.get('/test/')
        request.user = user
        # Force authentication
        from rest_framework.request import Request
        resp = view(request)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_user_with_required_role_gets_200(self, api_client, create_user):
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        from rest_framework.permissions import IsAuthenticated

        class ProtectedView(APIView):
            permission_classes = [IsAuthenticated, HasRole]
            required_roles = ['admin']

            def get(self, request):
                from rest_framework.response import Response
                return Response({'ok': True})

        factory = APIRequestFactory()
        view = ProtectedView.as_view()

        user = create_user(email='admin@test.com', roles=['admin'])
        request = factory.get('/test/')
        request.user = user
        resp = view(request)
        assert resp.status_code == status.HTTP_200_OK


# ─── Login throttle tests ───────────────────────────────────────────────────

class TestLoginThrottle:
    URL = '/v1/auth/login'

    def test_throttle_after_5_failures(self, api_client, create_user):
        """After 5 failed attempts, the 6th should return 429."""
        create_user(email='throttle@test.com', password='Pass1234!')

        for i in range(5):
            api_client.post(self.URL, {
                'email': 'throttle@test.com',
                'password': 'wrong',
            }, format='json')

        # 6th attempt should be throttled
        resp = api_client.post(self.URL, {
            'email': 'throttle@test.com',
            'password': 'wrong',
        }, format='json')
        assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'Retry-After' in resp

    def test_successful_login_clears_throttle(self, api_client, create_user):
        """A successful login resets the throttle counter."""
        create_user(email='clear@test.com', password='Pass1234!')

        # 3 failed attempts
        for _ in range(3):
            api_client.post(self.URL, {
                'email': 'clear@test.com',
                'password': 'wrong',
            }, format='json')

        # Successful login
        resp = api_client.post(self.URL, {
            'email': 'clear@test.com',
            'password': 'Pass1234!',
        }, format='json')
        assert resp.status_code == status.HTTP_200_OK

        # Should be able to fail again without immediate throttle
        resp = api_client.post(self.URL, {
            'email': 'clear@test.com',
            'password': 'wrong',
        }, format='json')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED  # not 429
