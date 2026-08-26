from django.contrib import admin
from .models import District, Need, Resource, Condition, MediaAttachment, Allocation, Alert


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'state', 'population']
    search_fields = ['name', 'state']


@admin.register(Need)
class NeedAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'urgency', 'quantity', 'unit', 'district', 'status', 'reported_by', 'created_at']
    list_filter = ['type', 'urgency', 'status', 'district']
    search_fields = ['description', 'unit']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'quantity_available', 'unit', 'district', 'verification_status', 'provider', 'updated_at']
    list_filter = ['type', 'verification_status', 'district']


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'condition_type', 'value', 'risk_score', 'district', 'source', 'reported_at']
    list_filter = ['condition_type', 'source', 'district']


@admin.register(MediaAttachment)
class MediaAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'media_type', 'need', 'condition', 'uploaded_at']


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'match', 'vehicle', 'delivery_status', 'estimated_delay_minutes', 'assigned_at', 'delivered_at']
    list_filter = ['delivery_status']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'alert_type', 'severity', 'district', 'channel', 'sent_at']
    list_filter = ['alert_type', 'severity', 'channel', 'district']
