"""
Direct in-process bridge between Django matching app and matching_engine Python package.
No network hop, zero-latency synchronous execution.
"""

from matching_engine.scoring import score_resources, score_single_resource, haversine_distance
from matching_engine.risk_model.predict import predict_risk, predict_route_risk, interpolate_route_waypoints
from matching_engine.weights_config import get_weights_for_type, WEIGHT_PROFILES

__all__ = [
    'score_resources',
    'score_single_resource',
    'haversine_distance',
    'predict_risk',
    'predict_route_risk',
    'interpolate_route_waypoints',
    'get_weights_for_type',
    'WEIGHT_PROFILES',
]
