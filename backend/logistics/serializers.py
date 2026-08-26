"""
Serializers for logistics and vehicle tracking app.
"""

from rest_framework import serializers
from .models import Vehicle
from core.spatial_compat import HAS_GIS
from core.serializers import GeoPointField

if HAS_GIS:
    from django.contrib.gis.geos import Point
else:
    from core.spatial_compat import MockPoint as Point


class VehicleSerializer(serializers.ModelSerializer):
    operator_username = serializers.CharField(source='operator.username', read_only=True)
    current_location = GeoPointField(required=False, allow_null=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Vehicle
        fields = [
            'id',
            'registration_number',
            'vehicle_type',
            'operator',
            'operator_username',
            'current_location',
            'latitude',
            'longitude',
            'last_ping_at',
            'status',
        ]
        read_only_fields = ['id', 'last_ping_at']

    def create(self, validated_data):
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            validated_data['current_location'] = Point(longitude, latitude)

        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated and 'operator' not in validated_data:
            validated_data['operator'] = request.user

        return super().create(validated_data)


class VehiclePingSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    status = serializers.ChoiceField(choices=Vehicle.STATUS_CHOICES, required=False)
