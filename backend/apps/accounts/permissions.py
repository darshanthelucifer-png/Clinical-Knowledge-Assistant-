"""
================================================================================
ClinSaarthi AI - Role-Based Permission Classes
================================================================================
What it does:
    Provides role-based access control (RBAC) classes for Django REST Framework views.
    Guarantees that sensitive actions (e.g. uploading clinical notes, viewing raw PII)
    are restricted to authorized healthcare personas.

Python Concepts Demonstrated:
    1. Polymorphic Interface Implementation: Overriding DRF's `BasePermission.has_permission`.
    2. Dynamic Factory Functions: Returning custom permission classes dynamically
       based on allowed role sets.
================================================================================
"""
from typing import List, Type
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from .models import User

class IsClinician(BasePermission):
    """Allows access only to authenticated users with the CLINICIAN role."""
    message = "Access restricted to certified Clinicians."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.CLINICIAN or request.user.is_superuser)
        )


class IsStudent(BasePermission):
    """Allows access to authenticated medical students and residents."""
    message = "Access restricted to registered Medical Students or Residents."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == User.Role.STUDENT or request.user.is_superuser)
        )


class IsAdminUserRole(BasePermission):
    """Allows access only to system administrators."""
    message = "Access restricted to System Administrators."

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_admin_role
        )


def require_roles(*allowed_roles: str) -> Type[BasePermission]:
    """
    Factory function demonstrating dynamic class generation.
    Returns a permission class that permits access if user possesses ANY of the given roles.

    Example:
        permission_classes = [require_roles('clinician', 'admin')]
    """
    class DynamicRolePermission(BasePermission):
        message = f"Access requires one of the following roles: {', '.join(allowed_roles)}"

        def has_permission(self, request: Request, view: APIView) -> bool:
            if not request.user or not request.user.is_authenticated:
                return False
            if request.user.is_superuser:
                return True
            return request.user.role in allowed_roles

    return DynamicRolePermission
