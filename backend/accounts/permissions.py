"""
Role-based and object-level permission classes for SETU API.
Enforces strict Broken Access Control (BAC) and Broken Object-Level Authorization (BOLA) safeguards.
"""

from rest_framework import permissions


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Allow read-only (GET, HEAD, OPTIONS) access for all users,
    but strictly require authenticated Admin or District Admin for state-modifying requests (POST, PUT, PATCH, DELETE).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['admin', 'district_admin'] or request.user.is_staff
            )
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['admin', 'district_admin'] or request.user.is_staff
            )
        )


class IsDistrictAdmin(permissions.BasePermission):
    """Only district admin or platform superadmin."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['district_admin', 'admin'] or request.user.is_staff
            )
        )

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['district_admin', 'admin'] or request.user.is_staff
            )
        )


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Read-only for public.
    Creation requires authentication.
    Modification (PUT, PATCH, DELETE) requires the object owner or an Administrator.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'district_admin'] or request.user.is_staff:
            return True
        # Check ownership on common relation fields
        owner = getattr(obj, 'reported_by', None) or getattr(obj, 'provider', None) or getattr(obj, 'operator', None)
        return owner == request.user


class IsFieldOfficerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Read-only for public.
    Reporting/updating conditions and hazard alerts strictly requires Field Officer or Administrator.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['field_officer', 'district_admin', 'admin'] or request.user.is_staff
            )
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'district_admin'] or request.user.is_staff:
            return True
        owner = getattr(obj, 'reported_by', None)
        return owner == request.user


class IsTransportOperatorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Read-only for public.
    Vehicle registration, GPS telemetry pings, and delivery allocations strictly require Transport Operator or Administrator.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role in ['transport_operator', 'district_admin', 'admin'] or request.user.is_staff
            )
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'district_admin'] or request.user.is_staff:
            return True
        owner = getattr(obj, 'operator', None)
        return owner == request.user


class IsVerifiedProviderOrReadOnly(permissions.BasePermission):
    """
    Read-only for public.
    Resource stockpile registration requires an authenticated, verified NGO/provider or Administrator.
    Modifications require the owner provider or an Administrator.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.is_verified or request.user.role in ['ngo', 'admin', 'district_admin']
            )
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'district_admin'] or request.user.is_staff:
            return True
        owner = getattr(obj, 'provider', None)
        return owner == request.user


class IsAssignedOperatorOrAdmin(IsTransportOperatorOrAdminOrReadOnly):
    """
    Strict object-level authorization for vehicle operations and GPS telemetry.
    Only the assigned driver/operator or an Administrator can modify/ping this vehicle.
    """
    pass


class IsOwnerOrAdmin(IsOwnerOrAdminOrReadOnly):
    """
    Strict object-level authorization for resource stockpiles and need reports.
    Only the original creator/provider or an Administrator can modify/delete.
    """
    pass


class IsDistrictAdminOrNodalAgency(IsDistrictAdmin):
    """
    Strict Broken Function Level Authorization protection for match confirmations and state-level dispatches.
    """
    pass
