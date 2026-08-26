"""
Views for matching app.
Handles triggering the matching engine, returning ranked candidates, and confirming matches.
"""

from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from core.models import Need, Allocation
from core.serializers import AllocationSerializer
from .models import Match
from .serializers import MatchSerializer, MatchConfirmSerializer
from .services import find_and_score_matches_for_need, confirm_match_and_allocate
from accounts.permissions import IsAdminUserOrReadOnly, IsDistrictAdmin, IsDistrictAdminOrNodalAgency


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve match proposals.
    GET /api/matches/ (Public read-only)
    GET /api/matches/{id}/ (Public read-only)
    POST /api/matches/{id}/confirm/ (District and Super Administrators only)
    """
    queryset = Match.objects.all().select_related('need', 'resource', 'allocation')
    serializer_class = MatchSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        need_id = self.request.query_params.get('need')
        status_param = self.request.query_params.get('status')
        if need_id:
            qs = qs.filter(need_id=need_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=True, methods=['post'], url_path='confirm', permission_classes=[IsDistrictAdminOrNodalAgency])
    def confirm_match_action(self, request, pk=None):
        """
        POST /api/matches/{id}/confirm/ (Admin only)
        Optional body: { "vehicle_id": 2 }
        Confirms match and creates Allocation.
        """
        match = self.get_object()
        serializer = MatchConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vehicle = serializer.validated_data.get('vehicle_id')
        allocation = confirm_match_and_allocate(match=match, vehicle=vehicle)

        return Response({
            'message': 'Match confirmed and resource allocated successfully.',
            'allocation': AllocationSerializer(allocation).data
        }, status=status.HTTP_200_OK)


class NeedMatchesView(APIView):
    """
    GET /api/needs/{id}/matches/
    Triggers the matching engine, discovers candidate resources,
    computes weighted scores + explanation breakdowns, and returns ranked matches.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, need_id=None):
        need = get_object_or_404(Need, pk=need_id)
        matches = find_and_score_matches_for_need(need)
        serializer = MatchSerializer(matches, many=True)
        return Response({
            'need_id': need.id,
            'need_type': need.type,
            'urgency': need.urgency,
            'quantity_required': need.quantity,
            'total_candidates_evaluated': len(matches),
            'matches': serializer.data,
        }, status=status.HTTP_200_OK)


class MatchConfirmStandaloneView(APIView):
    """
    POST /api/matches/{id}/confirm/
    Dedicated standalone endpoint to confirm match and create allocation (Admin only).
    """
    permission_classes = [IsDistrictAdmin]

    def post(self, request, match_id=None):
        match = get_object_or_404(Match, pk=match_id)
        serializer = MatchConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vehicle = serializer.validated_data.get('vehicle_id')
        allocation = confirm_match_and_allocate(match=match, vehicle=vehicle)

        return Response({
            'message': 'Match confirmed and resource allocated successfully.',
            'allocation': AllocationSerializer(allocation).data
        }, status=status.HTTP_200_OK)
