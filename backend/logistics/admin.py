from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'registration_number', 'vehicle_type', 'operator', 'status', 'last_ping_at']
    list_filter = ['status', 'vehicle_type']
    search_fields = ['registration_number', 'vehicle_type']
