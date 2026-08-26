"""
Serializers for core SETU domain models.
Handles GeoJSON point/polygon formatting, coordinate conversions, and relations.
"""

from rest_framework import serializers
from .models import (
    District, Need, Resource, Condition, MediaAttachment, Allocation, Alert, Institution
)
from .spatial_compat import HAS_GIS

if HAS_GIS:
    from django.contrib.gis.geos import Point
else:
    from .spatial_compat import MockPoint as Point


def _parse_location_input(data):
    """Extract location from either lat/lon fields or GeoJSON geometry object."""
    if isinstance(data, (list, tuple)) and len(data) >= 2:
        return Point(float(data[0]), float(data[1]))
    if isinstance(data, dict):
        if 'latitude' in data and 'longitude' in data:
            return Point(float(data['longitude']), float(data['latitude']))
        elif 'lat' in data and 'lon' in data:
            return Point(float(data['lon']), float(data['lat']))
        elif data.get('type') == 'Point' and 'coordinates' in data:
            coords = data['coordinates']
            return Point(float(coords[0]), float(coords[1]))
    return None


def _format_point_output(point):
    """Format Point object to clean GeoJSON & lat/lon dict."""
    if point is None:
        return None
    if hasattr(point, 'coords'):
        coords = point.coords
        return {
            'type': 'Point',
            'coordinates': [float(coords[0]), float(coords[1])],
            'latitude': float(coords[1]),
            'longitude': float(coords[0]),
        }
    elif isinstance(point, dict) and 'coordinates' in point:
        coords = point['coordinates']
        return {
            'type': 'Point',
            'coordinates': coords,
            'latitude': float(coords[1]) if len(coords) > 1 else None,
            'longitude': float(coords[0]) if len(coords) > 0 else None,
        }
    return None


class GeoPointField(serializers.Field):
    """Custom serializer field for Point geometry."""
    def to_representation(self, value):
        return _format_point_output(value)

    def to_internal_value(self, data):
        point = _parse_location_input(data)
        if point is None:
            raise serializers.ValidationError(
                'Invalid coordinate format. Expected {"type": "Point", "coordinates": [lon, lat]} or {"latitude": lat, "longitude": lon}'
            )
        return point


class MediaAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAttachment
        fields = ['id', 'need', 'condition', 'file', 'media_type', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class DistrictSerializer(serializers.ModelSerializer):
    centroid = GeoPointField(required=False, allow_null=True)
    open_needs_count = serializers.SerializerMethodField()
    available_resources_count = serializers.SerializerMethodField()

    class Meta:
        model = District
        fields = [
            'id',
            'name',
            'state',
            'boundary',
            'centroid',
            'population',
            'open_needs_count',
            'available_resources_count',
        ]

    def get_open_needs_count(self, obj):
        return obj.needs.filter(status='open').count()

    def get_available_resources_count(self, obj):
        return obj.resources.filter(quantity_available__gt=0).count()


class NeedSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.CharField(source='reported_by.username', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    location = GeoPointField(required=False, allow_null=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    attachments = MediaAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Need
        fields = [
            'id',
            'type',
            'location',
            'latitude',
            'longitude',
            'district',
            'district_name',
            'urgency',
            'quantity',
            'unit',
            'description',
            'reported_by',
            'reported_by_username',
            'status',
            'attachments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'reported_by': {'required': False},
        }

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude)
        elif validated_data.get('location') is None:
            validated_data['location'] = Point(92.78, 24.83)

        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and 'reported_by' not in validated_data:
            validated_data['reported_by'] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude)
        return super().update(instance, validated_data)


class ResourceSerializer(serializers.ModelSerializer):
    provider_username = serializers.CharField(source='provider.username', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    location = GeoPointField(required=False, allow_null=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Resource
        fields = [
            'id',
            'type',
            'location',
            'latitude',
            'longitude',
            'district',
            'district_name',
            'quantity_available',
            'unit',
            'provider',
            'provider_username',
            'verification_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'provider': {'required': False},
        }

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude)
        elif validated_data.get('location') is None:
            validated_data['location'] = Point(92.78, 24.83)

        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and 'provider' not in validated_data:
            validated_data['provider'] = request.user
            if request.user.is_verified:
                validated_data['verification_status'] = 'verified_org'

        return super().create(validated_data)

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude)
        return super().update(instance, validated_data)


class ConditionSerializer(serializers.ModelSerializer):
    reported_by_username = serializers.CharField(source='reported_by.username', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True)
    location = GeoPointField(required=False, allow_null=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    attachments = MediaAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Condition
        fields = [
            'id',
            'location',
            'latitude',
            'longitude',
            'district',
            'district_name',
            'condition_type',
            'value',
            'risk_score',
            'reported_by',
            'reported_by_username',
            'source',
            'attachments',
            'reported_at',
        ]
        read_only_fields = ['id', 'reported_at']
        extra_kwargs = {
            'reported_by': {'required': False},
        }

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude)
        elif validated_data.get('location') is None:
            validated_data['location'] = Point(92.78, 24.83)

        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and 'reported_by' not in validated_data:
            validated_data['reported_by'] = request.user

        return super().create(validated_data)


class AllocationSerializer(serializers.ModelSerializer):
    match_score = serializers.FloatField(source='match.score', read_only=True)
    need_type = serializers.CharField(source='match.need.type', read_only=True)
    need_quantity = serializers.IntegerField(source='match.need.quantity', read_only=True)
    need_unit = serializers.CharField(source='match.need.unit', read_only=True)
    resource_provider = serializers.CharField(source='match.resource.provider.username', read_only=True)
    vehicle_registration = serializers.CharField(source='vehicle.registration_number', read_only=True)
    vehicle_type = serializers.CharField(source='vehicle.vehicle_type', read_only=True)

    class Meta:
        model = Allocation
        fields = [
            'id',
            'match',
            'match_score',
            'need_type',
            'need_quantity',
            'need_unit',
            'resource_provider',
            'vehicle',
            'vehicle_registration',
            'vehicle_type',
            'route_geojson',
            'estimated_delay_minutes',
            'delivery_status',
            'assigned_at',
            'delivered_at',
        ]
        read_only_fields = ['id', 'assigned_at']


class AlertSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id',
            'alert_type',
            'related_condition',
            'related_allocation',
            'district',
            'district_name',
            'message',
            'severity',
            'language',
            'channel',
            'sent_at',
        ]
        read_only_fields = ['id', 'sent_at']


class InstitutionSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    location = GeoPointField(required=False, allow_null=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Institution
        fields = [
            'id',
            'name',
            'category',
            'facility_type',
            'district',
            'district_name',
            'state',
            'location',
            'latitude',
            'longitude',
            'address',
            'contact_number',
            'emergency_helpline',
            'bed_capacity',
            'is_auto_ingested',
            'source_api',
            'operational_status',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['location'] = Point(longitude, latitude)
        return super().create(validated_data)

