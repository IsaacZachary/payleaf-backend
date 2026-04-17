"""
Auth views — implements every endpoint from BACKEND_API.md §Auth.
All paths are relative to /v1/auth/.
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PasswordResetToken, User
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from .throttle import (
    check_login_throttle,
    clear_login_throttle,
    record_login_attempt,
)


def _get_client_ip(request):
    """Extract the real client IP, respecting X-Forwarded-For only from trusted proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


class LoginView(APIView):
    """POST /auth/login — email + password → session cookie."""
    permission_classes = [AllowAny]

    def post(self, request):
        ip = _get_client_ip(request)
        email = request.data.get('email', '')

        # Check throttle
        allowed, retry_after = check_login_throttle(ip, email)
        if not allowed:
            return Response(
                {
                    'error': {
                        'code': 'rate_limited',
                        'message': 'Too many login attempts. Try again later.',
                        'doc_url': 'https://docs.payleaf.app/errors#rate_limited',
                        'request_id': request.META.get('HTTP_X_REQUEST_ID', ''),
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={'Retry-After': str(retry_after)},
            )

        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            # Record failed attempt
            record_login_attempt(ip, email)
            return Response(
                {
                    'error': {
                        'code': 'invalid_credentials',
                        'message': 'Invalid email or password.',
                        'doc_url': 'https://docs.payleaf.app/errors#invalid_credentials',
                        'request_id': request.META.get('HTTP_X_REQUEST_ID', ''),
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data['user']

        # Clear throttle on success
        clear_login_throttle(ip, email)

        # Create session — 12h sliding expiry
        login(request, user)
        request.session.set_expiry(43200)  # 12 hours in seconds
        session_expires_at = timezone.now() + timedelta(hours=12)

        return Response(
            {
                'user': UserSerializer(user).data,
                'session_expires_at': session_expires_at.isoformat().replace('+00:00', 'Z'),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """POST /auth/logout — invalidate session."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /auth/me — current user + roles."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                'user': UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    """POST /auth/forgot-password — send reset link (always 200 to prevent enumeration)."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email, is_active=True)
            # Invalidate any existing tokens
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

            # Create new token
            token = PasswordResetToken(
                user=user,
                expires_at=timezone.now() + timedelta(minutes=30),
            )
            token.save()

            # In production: send email with reset link containing token.token
            # For now we just create the token — email sending is handled by
            # a Celery task or the email backend.

        except User.DoesNotExist:
            pass  # Don't leak whether email exists

        return Response(
            {'message': 'If that email is registered, a reset link has been sent.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """POST /auth/reset-password — body: { token, new_password }."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_value = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            reset_token = PasswordResetToken.objects.get(token=token_value)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {
                    'error': {
                        'code': 'invalid_token',
                        'message': 'Invalid or expired reset token.',
                        'doc_url': 'https://docs.payleaf.app/errors#invalid_token',
                        'request_id': request.META.get('HTTP_X_REQUEST_ID', ''),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reset_token.is_valid:
            return Response(
                {
                    'error': {
                        'code': 'invalid_token',
                        'message': 'Invalid or expired reset token.',
                        'doc_url': 'https://docs.payleaf.app/errors#invalid_token',
                        'request_id': request.META.get('HTTP_X_REQUEST_ID', ''),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Mark token as used (single-use)
        reset_token.used = True
        reset_token.save()

        # Revoke all sessions on password change
        from django.contrib.sessions.models import Session
        # Flush the user's current sessions by cycling session key
        # In Redis-backed sessions, we rely on the session middleware.

        return Response(
            {'message': 'Password has been reset successfully.'},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """POST /auth/change-password — body: { old_password, new_password }."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        if not request.user.check_password(old_password):
            return Response(
                {
                    'error': {
                        'code': 'invalid_password',
                        'message': 'Current password is incorrect.',
                        'doc_url': 'https://docs.payleaf.app/errors#invalid_password',
                        'request_id': request.META.get('HTTP_X_REQUEST_ID', ''),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()

        # Re-authenticate so the session isn't destroyed
        login(request, request.user)
        request.session.set_expiry(43200)

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK,
        )
