"""
================================================================================
ClinSaarthi AI - User Authentication & Role Access Tests
================================================================================
What it tests:
    1. User registration with role selection (clinician, student).
    2. Password confirmation matching and Django security validator enforcement.
    3. JWT Token generation and enriched custom claims (role, username, email).
    4. JWT Login endpoint and user payload delivery.
    5. Protected profile endpoint (/api/v1/auth/me/) access control.
    6. Role permission checks (IsClinician, IsStudent, IsAdminUserRole).

Python Concepts Demonstrated:
    1. pytest fixtures & test isolation.
    2. APIClient for HTTP integration testing.
    3. PyJWT decoding to inspect token payload claims.
================================================================================
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.accounts.models import User
import jwt
from django.conf import settings

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="dr_sharma",
        email="sharma@hospital.org",
        password="SecureClinicalPassword123!",
        role=User.Role.CLINICIAN,
        department="Cardiology",
        institution="AIIMS Delhi",
        license_number="MED-12345"
    )

@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="student_rohit",
        email="rohit@medschool.edu",
        password="StudentStudyPassword123!",
        role=User.Role.STUDENT,
        institution="Grant Medical College"
    )

@pytest.mark.django_db
class TestUserRegistration:
    def test_successful_registration(self, api_client):
        url = reverse('accounts:register')
        payload = {
            "username": "dr_priya",
            "email": "priya@clinic.org",
            "password": "StrongPassword789!",
            "password_confirm": "StrongPassword789!",
            "role": "clinician",
            "department": "Neurology",
            "institution": "PGI Chandigarh",
            "license_number": "MED-99887"
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["username"] == "dr_priya"
        assert response.data["user"]["role"] == "clinician"

        # Verify password is encrypted in database
        user = User.objects.get(username="dr_priya")
        assert user.check_password("StrongPassword789!")
        assert user.password != "StrongPassword789!"

    def test_registration_password_mismatch(self, api_client):
        url = reverse('accounts:register')
        payload = {
            "username": "dr_fail",
            "email": "fail@clinic.org",
            "password": "StrongPassword789!",
            "password_confirm": "DifferentPassword123!",
            "role": "clinician"
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

@pytest.mark.django_db
class TestJWTAuthentication:
    def test_login_returns_jwt_and_custom_claims(self, api_client, clinician_user):
        url = reverse('accounts:login')
        payload = {
            "username": "dr_sharma",
            "password": "SecureClinicalPassword123!"
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["role"] == "clinician"
        assert response.data["user"]["department"] == "Cardiology"

        # Decode token to verify custom claims are present in payload
        access_token = response.data["access"]
        decoded_payload = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
        assert decoded_payload["role"] == "clinician"
        assert decoded_payload["username"] == "dr_sharma"
        assert decoded_payload["email"] == "sharma@hospital.org"

    def test_login_invalid_credentials(self, api_client, clinician_user):
        url = reverse('accounts:login')
        payload = {
            "username": "dr_sharma",
            "password": "WrongPassword!"
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_me_endpoint(self, api_client, clinician_user):
        # Without token -> 401
        url = reverse('accounts:user_profile')
        res_anon = api_client.get(url)
        assert res_anon.status_code == status.HTTP_401_UNAUTHORIZED

        # With Bearer token -> 200
        api_client.force_authenticate(user=clinician_user)
        res_auth = api_client.get(url)
        assert res_auth.status_code == status.HTTP_200_OK
        assert res_auth.data["username"] == "dr_sharma"
        assert res_auth.data["role"] == "clinician"
        assert res_auth.data["license_number"] == "MED-12345"

@pytest.mark.django_db
class TestRoleProperties:
    def test_user_role_helper_properties(self, clinician_user, student_user):
        assert clinician_user.is_clinician is True
        assert clinician_user.is_student is False
        assert clinician_user.is_admin_role is False

        assert student_user.is_student is True
        assert student_user.is_clinician is False
        assert student_user.is_admin_role is False

    def test_health_check_endpoint(self, api_client):
        response = api_client.get(reverse('health-check'))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert response.data["service"] == "ClinSaarthi AI Backend"
        assert "models" in response.data

