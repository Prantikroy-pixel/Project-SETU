"""
User model for SETU accounts.
Extends AbstractUser with role, phone, preferred_language, district FK, and verification status.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_FIELD_OFFICER = 'field_officer'
    ROLE_TRANSPORT_OPERATOR = 'transport_operator'
    ROLE_DISTRICT_ADMIN = 'district_admin'
    ROLE_CITIZEN = 'citizen'
    ROLE_NGO = 'ngo'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_FIELD_OFFICER, 'Field Officer'),
        (ROLE_TRANSPORT_OPERATOR, 'Transport Operator'),
        (ROLE_DISTRICT_ADMIN, 'District Admin'),
        (ROLE_CITIZEN, 'Citizen'),
        (ROLE_NGO, 'NGO'),
        (ROLE_ADMIN, 'Admin'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=ROLE_CITIZEN,
        help_text="Role determining permissions across the platform"
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Contact number for SMS dispatch alerts"
    )
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        help_text="Preferred language code for notifications (e.g. en, as, bn, hi)"
    )
    district = models.ForeignKey(
        'core.District',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Assigned home or duty district"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Trust verification for verified NGOs, agencies, or transport providers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"