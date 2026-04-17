from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                {'detail': 'Invalid email or password.'},
                code='invalid_credentials',
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': 'Account is disabled.'},
                code='account_disabled',
            )

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'roles', 'created_at']
        read_only_fields = fields

    def get_id(self, obj):
        return obj.prefixed_id

    def get_roles(self, obj):
        return obj.roles


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
