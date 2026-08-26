from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'phone_number', 'district', 'is_verified', 'is_staff']
    list_filter = ['role', 'is_verified', 'district', 'preferred_language']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('SETU Profile', {
            'fields': ('role', 'phone_number', 'preferred_language', 'district', 'is_verified')
        }),
    )
