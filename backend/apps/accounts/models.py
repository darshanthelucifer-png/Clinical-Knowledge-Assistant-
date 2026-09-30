"""
================================================================================
ClinSaarthi AI - User Account & Role Models
================================================================================
What it does:
    Defines the custom User entity extending Django's AbstractUser with
    clinical role-based access control (clinician, student, admin) and professional
    attributes (department, license number, medical institution).

Python Concepts Demonstrated:
    1. OOP Inheritance: Subclassing Django's AbstractUser to extend authentication
       without rewriting password hashing, session tokens, or permission trees.
    2. Python Enums & Models.TextChoices: Strongly-typed, clean enumerations for
       database choices that prevent string typos and aid IDE autocompletion.
    3. Python Property Decorators (@property): Exposing convenient boolean checks
       (e.g., user.is_clinician) as computed attributes.
================================================================================
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom user model for ClinSaarthi AI.
    Differentiates clinician, student, and admin permissions across the RAG system.
    """
    class Role(models.TextChoices):
        CLINICIAN = 'clinician', _('Clinician (Doctor / Nurse / Specialist)')
        STUDENT = 'student', _('Medical Student / Resident')
        ADMIN = 'admin', _('System Administrator')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text=_('User role determining access levels and permissions in the system.')
    )
    department = models.CharField(
        max_length=120,
        blank=True,
        help_text=_('Clinical specialty or academic department (e.g., Cardiology, Oncology).')
    )
    institution = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Hospital, medical university, or research organization.')
    )
    license_number = models.CharField(
        max_length=80,
        blank=True,
        help_text=_('Professional medical license number (optional for student users).')
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_clinician(self) -> bool:
        """Returns True if the user has the Clinician role."""
        return self.role == self.Role.CLINICIAN

    @property
    def is_student(self) -> bool:
        """Returns True if the user has the Student role."""
        return self.role == self.Role.STUDENT

    @property
    def is_admin_role(self) -> bool:
        """Returns True if user has the Admin role or is a Django superuser/staff."""
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser
