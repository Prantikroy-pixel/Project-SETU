"""
Scoring Algorithm for SETU Matching Engine.
Evaluates candidate resources against a specific need using multi-criteria weighted logic.
"""

import math
from typing import Any, Dict, List, Optional, Union
from .weights_config import get_weights_for_type

URGENCY_SCORES = {
    'critical': 1.0,
    'high': 0.8,
    'medium': 0.5,
    'low': 0.2,
}

VERIFICATION_SCORES = {
    'verified_org': 1.0,
    'verified': 1.0,
    'unverified': 0.5,
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in kilometers between two points on the Earth."""
    r = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def _extract_coord(obj: Any) -> Optional[tuple]:
    """Extract (latitude, longitude) from object or dict."""
    if isinstance(obj, dict):
        if 'latitude' in obj and 'longitude' in obj:
            return float(obj['latitude']), float(obj['longitude'])
        if 'lat' in obj and 'lon' in obj:
            return float(obj['lat']), float(obj['lon'])
        if 'location' in obj and hasattr(obj['location'], 'coords'):
            # GeoDjango Point coords are (x/lon, y/lat)
            coords = obj['location'].coords
            return float(coords[1]), float(coords[0])
    else:
        if hasattr(obj, 'latitude') and hasattr(obj, 'longitude'):
            return float(obj.latitude), float(obj.longitude)
        if hasattr(obj, 'lat') and hasattr(obj, 'lon'):
            return float(obj.lat), float(obj.lon)
        if hasattr(obj, 'location') and hasattr(obj.location, 'coords'):
            coords = obj.location.coords
            return float(coords[1]), float(coords[0])
    return None


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to extract attribute or dict key."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def calculate_proximity_score(distance_km: float, half_life_km: float = 25.0) -> float:
    """
    Calculate proximity score using exponential decay.
    At distance 0 km -> score 1.0
    At distance half_life_km (default 25km) -> score 0.5
    """
    if distance_km <= 0:
        return 1.0
    # decay constant lambda = ln(2) / half_life
    decay_constant = math.log(2) / half_life_km
    score = math.exp(-decay_constant * distance_km)
    return max(0.0, min(1.0, score))


def score_single_resource(
    need: Any,
    candidate: Any,
    weights: Dict[str, float],
    distance_km: Optional[float] = None,
    condition_risk: float = 0.0,
) -> Dict[str, Any]:
    """
    Score a single candidate resource against a need.
    Returns composite score and granular breakdown.
    """
    # 1. Urgency score
    urgency_raw = str(_get_val(need, 'urgency', 'medium')).lower()
    urgency_score = URGENCY_SCORES.get(urgency_raw, 0.5)

    # 2. Proximity score
    if distance_km is None:
        need_coords = _extract_coord(need)
        cand_coords = _extract_coord(candidate)
        if need_coords and cand_coords:
            distance_km = haversine_distance(
                need_coords[0], need_coords[1], cand_coords[0], cand_coords[1]
            )
        else:
            cand_dist = _get_val(candidate, 'distance_km', None)
            if cand_dist is not None:
                distance_km = float(cand_dist)
            else:
                distance_km = 10.0  # default neutral fallback

    proximity_score = calculate_proximity_score(distance_km)

    # 3. Verification score
    verification_raw = str(_get_val(candidate, 'verification_status', 'unverified')).lower()
    if isinstance(_get_val(candidate, 'verification_status'), bool):
        verification_score = 1.0 if _get_val(candidate, 'verification_status') else 0.5
    else:
        verification_score = VERIFICATION_SCORES.get(verification_raw, 0.5)

    # 4. Quantity fit score
    need_qty = float(_get_val(need, 'quantity', 1))
    cand_qty = float(_get_val(candidate, 'quantity_available', _get_val(candidate, 'quantity', 0)))
    if need_qty <= 0:
        quantity_fit_score = 1.0
    else:
        ratio = cand_qty / need_qty
        if ratio >= 1.0:
            quantity_fit_score = 1.0
        else:
            quantity_fit_score = max(0.1, ratio * 0.95)

    # 5. Delay risk / route hazard score (1.0 = safe/no hazard, 0.0 = severe hazard)
    cand_risk = float(_get_val(candidate, 'condition_risk', condition_risk))
    delay_risk_score = max(0.0, min(1.0, 1.0 - cand_risk))

    # Calculate weighted composite score
    breakdown = {
        'urgency': round(urgency_score, 4),
        'proximity': round(proximity_score, 4),
        'verification': round(verification_score, 4),
        'quantity_fit': round(quantity_fit_score, 4),
        'delay_risk': round(delay_risk_score, 4),
        'distance_km': round(distance_km, 2) if distance_km is not None else None,
    }

    composite_score = (
        weights.get('urgency', 0.25) * urgency_score
        + weights.get('proximity', 0.25) * proximity_score
        + weights.get('verification', 0.20) * verification_score
        + weights.get('quantity_fit', 0.20) * quantity_fit_score
        + weights.get('delay_risk', 0.10) * delay_risk_score
    )

    composite_score = max(0.0, min(1.0, composite_score))

    resource_id = _get_val(candidate, 'id', _get_val(candidate, 'resource_id'))

    return {
        'resource_id': resource_id,
        'resource': candidate,
        'score': round(composite_score, 4),
        'score_breakdown': breakdown,
    }


def score_resources(
    need: Any,
    candidates: List[Any],
    weights_override: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Score and rank a list of candidate resources for a given need.
    Returns ranked list sorted by score descending.
    """
    if not candidates:
        return []

    need_type = str(_get_val(need, 'type', 'other')).lower()
    weights = weights_override or get_weights_for_type(need_type)

    results = []
    for cand in candidates:
        scored = score_single_resource(need, cand, weights)
        results.append(scored)

    # Sort descending by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results
