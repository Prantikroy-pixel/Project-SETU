"""
Orchestration service for PostGIS candidate querying, matching engine scoring, and match confirmation.
"""

from typing import List, Optional
from django.db import transaction
from core.models import Need, Resource, Allocation, Condition
from logistics.models import Vehicle
from core.services import generate_route_geojson
from core.spatial_compat import HAS_GIS
from .models import Match
from .engine import score_resources, haversine_distance, predict_risk, predict_route_risk


def _get_coords_from_point(point):
    """Extract (lat, lon) tuple from point."""
    if point is None:
        return (24.8333, 92.7789)
    if hasattr(point, 'coords'):
        coords = point.coords
        return (float(coords[1]), float(coords[0]))
    if isinstance(point, dict) and 'coordinates' in point:
        coords = point['coordinates']
        return (float(coords[1]), float(coords[0]))
    return (24.8333, 92.7789)


def find_and_score_matches_for_need(need: Need, max_candidates: int = 50) -> List[Match]:
    """
    1. Queries candidate Resources with matching type and available quantity.
    2. Runs spatial proximity and hazard assessments.
    3. Feeds candidates into matching_engine.scoring.
    4. Upserts Match records in DB.
    5. Returns ordered Match instances.
    """
    candidates = Resource.objects.filter(
        type=need.type,
        quantity_available__gt=0
    ).select_related('provider', 'district')

    need_lat, need_lon = _get_coords_from_point(need.location)

    candidate_list = []
    for cand in candidates:
        cand_lat, cand_lon = _get_coords_from_point(cand.location)
        dist_km = haversine_distance(need_lat, need_lon, cand_lat, cand_lon)

        # Check for active hazards in candidate's district
        cand_risk = 0.0
        if cand.district:
            hazards = Condition.objects.filter(
                district=cand.district,
                condition_type__in=['road_status', 'landslide_risk']
            ).order_by('-reported_at')[:3]
            for h in hazards:
                if h.condition_type == 'road_status' and h.value.lower() in ['blocked', 'flooded', 'landslide']:
                    cand_risk = max(cand_risk, 0.8)
                elif h.risk_score:
                    cand_risk = max(cand_risk, h.risk_score)

        # Evaluate ML real-time corridor hazard risk across the entire transit range from candidate to need
        if cand_risk == 0.0 and cand_lat and cand_lon and need_lat and need_lon:
            try:
                transit_pts = [
                    (cand_lat, cand_lon),
                    ((cand_lat + need_lat) / 2.0, (cand_lon + need_lon) / 2.0),
                    (need_lat, need_lon)
                ]
                route_res = predict_route_risk(waypoints=transit_pts, use_realtime=True)
                cand_risk = float(route_res.get('route_composite_risk', 0.0))
            except Exception:
                pass

        candidate_list.append({
            'id': cand.id,
            'resource_obj': cand,
            'type': cand.type,
            'quantity_available': cand.quantity_available,
            'verification_status': cand.verification_status,
            'latitude': cand_lat,
            'longitude': cand_lon,
            'distance_km': dist_km,
            'condition_risk': cand_risk,
        })

    # Run matching engine scoring algorithm
    need_dict = {
        'id': need.id,
        'type': need.type,
        'urgency': need.urgency,
        'quantity': need.quantity,
        'latitude': need_lat,
        'longitude': need_lon,
    }

    scored_results = score_resources(need_dict, candidate_list)

    # Persist or update Match rows in the database
    matches = []
    with transaction.atomic():
        for res in scored_results[:max_candidates]:
            cand_dict = res['resource']
            resource_obj = cand_dict['resource_obj']
            score = res['score']
            score_breakdown = res['score_breakdown']

            match_obj, _ = Match.objects.update_or_create(
                need=need,
                resource=resource_obj,
                defaults={
                    'score': score,
                    'score_breakdown': score_breakdown,
                }
            )
            matches.append(match_obj)

    # Sort matches by score descending
    matches.sort(key=lambda m: m.score, reverse=True)
    return matches


def confirm_match_and_allocate(match: Match, vehicle: Optional[Vehicle] = None) -> Allocation:
    """
    Confirms a match, links/creates the Allocation, generates route geometry,
    and updates Need and Vehicle statuses.
    """
    with transaction.atomic():
        match.status = Match.STATUS_CONFIRMED
        match.save(update_fields=['status'])

        need = match.need
        need.status = 'matched'
        need.save(update_fields=['status'])

        # Compute route geometry
        need_coords = _get_coords_from_point(need.location)
        res_coords = _get_coords_from_point(match.resource.location)
        route_geojson = generate_route_geojson(res_coords, need_coords)

        # Create or update allocation
        allocation, _ = Allocation.objects.update_or_create(
            match=match,
            defaults={
                'vehicle': vehicle,
                'route_geojson': route_geojson,
                'delivery_status': 'dispatched' if vehicle else 'matched',
            }
        )

        if vehicle:
            vehicle.status = Vehicle.STATUS_EN_ROUTE
            vehicle.save(update_fields=['status'])

        return allocation
