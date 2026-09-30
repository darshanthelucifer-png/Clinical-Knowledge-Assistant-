"""
================================================================================
ClinSaarthi AI - Account Serializers
================================================================================
What it does:
    Handles serialization, deserialization, and validation of user credentials,
    role assignments, and enriched JWT token claims.

Python Concepts Demonstrated:
    1. Data Transfer Objects (DTOs) & Validation: DRF serializers validate input
       types and business logic (e.g., password matching, role validation).
    2. Overriding Class Methods: Extending SimpleJWT's TokenObtainPairSerializer
       to inject custom claims (role, username) into the cryptographically signed JWT payload.
    3. Type Annotations: Full typing throughout serializers for code reliability.
================================================================================
"""
from typing import Any, Dict
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Public representation of user profiles.
    Excludes sensitive fields like password hashes.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'department',
            'institution',
            'license_number',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'role_display']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles user signup with role selection, password confirmation,
    and validation according to Django's security validators.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
            'department',
            'institution',
            'license_number'
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that password and password_confirm match."""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        """Create a new user with securely hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that embeds user roles and metadata directly into the JWT token
    payload and returns the user profile in the authentication response body.
    """
    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        # Add custom claims to the JWT payload
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        data = super().validate(attrs)
        # Include serialized user info in the JSON response body
        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        return data
