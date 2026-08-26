"""
Serializers for matching app.
Handles Match list presentation, score explainability payload, and match confirmation requests.
"""

from rest_framework import serializers
from .models import Match
from core.serializers import NeedSerializer, ResourceSerializer, AllocationSerializer
from logistics.models import Vehicle


class MatchSerializer(serializers.ModelSerializer):
    need_details = NeedSerializer(source='need', read_only=True)
    resource_details = ResourceSerializer(source='resource', read_only=True)
    allocation = AllocationSerializer(read_only=True)

    class Meta:
        model = Match
        fields = [
            'id',
            'need',
            'need_details',
            'resource',
            'resource_details',
            'score',
            'score_breakdown',
            'status',
            'allocation',
            'created_at',
        ]
        read_only_fields = ['id', 'score', 'score_breakdown', 'created_at']


class MatchConfirmSerializer(serializers.Serializer):
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        required=False,
        allow_null=True
    )
