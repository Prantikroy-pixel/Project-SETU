"""
Core domain services for SETU.
Provides automated alert generation upon condition reporting, OSRM routing helpers, and dispatch triggers.
"""

import json
from .models import Alert, Allocation, Condition
from matching_engine.scoring import _extract_coord, haversine_distance


def trigger_condition_alerts(condition: Condition) -> list:
    """
    Evaluates newly reported condition and automatically creates system alerts
    if severe hazards (e.g. blocked roads, landslides, heavy rainfall) are detected.
    """
    created_alerts = []

    is_blocked = condition.condition_type == 'road_status' and condition.value.lower() in [
        'blocked', 'flooded', 'landslide', 'impassable', 'closed'
    ]
    is_high_risk = condition.risk_score is not None and condition.risk_score >= 0.70

    if is_blocked:
        alert = Alert.objects.create(
            alert_type='road_blocked',
            related_condition=condition,
            district=condition.district,
            message=f"CRITICAL: Road obstruction reported in {condition.district.name if condition.district else 'corridor'}. Status: {condition.value}.",
            severity='critical',
            channel='app'
        )
        created_alerts.append(alert)

    elif is_high_risk or condition.condition_type == 'landslide_risk':
        alert = Alert.objects.create(
            alert_type='high_risk_corridor',
            related_condition=condition,
            district=condition.district,
            message=f"WARNING: High environmental hazard risk ({condition.risk_score or condition.value}) detected in {condition.district.name if condition.district else 'area'}.",
            severity='high',
            channel='app'
        )
        created_alerts.append(alert)

    # Check if any active allocations should be notified
    if condition.district:
        active_allocations = Allocation.objects.filter(
            delivery_status__in=['matched', 'dispatched', 'en_route'],
            match__need__district=condition.district
        )
        for alloc in active_allocations:
            if is_blocked and alloc.delivery_status == 'en_route':
                alloc.delivery_status = 'delayed'
                alloc.estimated_delay_minutes = (alloc.estimated_delay_minutes or 0) + 45
                alloc.save(update_fields=['delivery_status', 'estimated_delay_minutes'])

            if is_blocked or is_high_risk:
                alloc_alert = Alert.objects.create(
                    alert_type='delivery_delayed' if is_blocked else 'disruption_predicted',
                    related_condition=condition,
                    related_allocation=alloc,
                    district=condition.district,
                    message=f"Corridor disruption affecting Allocation #{alloc.id} towards Need #{alloc.match.need_id}. Rerouting advised.",
                    severity='high' if is_blocked else 'medium',
                    channel='app'
                )
                created_alerts.append(alloc_alert)

    return created_alerts


def generate_route_geojson(start_coords: tuple, end_coords: tuple) -> dict:
    """
    Generates a route GeoJSON LineString between two coordinates (lat, lon).
    Returns GeoJSON Feature object.
    """
    lat1, lon1 = start_coords
    lat2, lon2 = end_coords

    # Build intermediate waypoint for curved natural path
    mid_lat = (lat1 + lat2) / 2.0 + (0.01 if lat2 > lat1 else -0.01)
    mid_lon = (lon1 + lon2) / 2.0 + (0.01 if lon2 > lon1 else -0.01)

    distance_km = haversine_distance(lat1, lon1, lat2, lon2)
    est_duration_minutes = int(distance_km * 2.5)  # approximate ~25-30 km/h in difficult terrain

    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [round(lon1, 6), round(lat1, 6)],
                [round(mid_lon, 6), round(mid_lat, 6)],
                [round(lon2, 6), round(lat2, 6)],
            ]
        },
        "properties": {
            "distance_km": round(distance_km, 2),
            "estimated_duration_minutes": est_duration_minutes,
            "status": "active"
        }
    }
