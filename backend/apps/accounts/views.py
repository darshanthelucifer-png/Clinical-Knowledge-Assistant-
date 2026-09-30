"""
================================================================================
ClinSaarthi AI - Account & Authentication Views
================================================================================
What it does:
    Exposes endpoints for user registration, JWT login with enriched role claims,
    and profile retrieval.

Python Concepts Demonstrated:
    1. Thin Views Architecture: Views only validate request payloads via serializers
       and return standardized HTTP status codes. Business logic is not coupled to views.
    2. Class-Based Views (CBVs): Leveraging DRF generics (`CreateAPIView`, `RetrieveUpdateAPIView`)
       for concise, readable, and highly maintainable endpoint handlers.
================================================================================
"""
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer
)

class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Registers a new user (clinician or student), immediately generating and returning
    JWT access/refresh tokens alongside the user profile.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens immediately so the frontend can auto-login after signup
        refresh = RefreshToken.for_user(user)
        refresh['role'] = user.role
        refresh['username'] = user.username
        refresh['email'] = user.email

        user_data = UserSerializer(user).data

        return Response({
            "message": "User registered successfully.",
            "user": user_data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Authenticates username/password and returns access + refresh JWT tokens
    plus the serialized user profile with role metadata.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/v1/auth/me/
    Retrieves or updates the authenticated user's profile and medical attributes.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user
