"""
Weights Configuration for SETU Matching Engine.
Defines category-specific scoring weight profiles.
"""

WEIGHT_PROFILES = {
    'medicine': {
        'urgency': 0.35,
        'proximity': 0.30,
        'verification': 0.20,
        'quantity_fit': 0.10,
        'delay_risk': 0.05,
    },
    'water': {
        'urgency': 0.30,
        'proximity': 0.35,
        'verification': 0.15,
        'quantity_fit': 0.15,
        'delay_risk': 0.05,
    },
    'food': {
        'urgency': 0.25,
        'proximity': 0.25,
        'verification': 0.15,
        'quantity_fit': 0.25,
        'delay_risk': 0.10,
    },
    'construction_material': {
        'urgency': 0.15,
        'proximity': 0.20,
        'verification': 0.15,
        'quantity_fit': 0.40,
        'delay_risk': 0.10,
    },
    'agricultural_produce': {
        'urgency': 0.20,
        'proximity': 0.30,
        'verification': 0.15,
        'quantity_fit': 0.25,
        'delay_risk': 0.10,
    },
    'other': {
        'urgency': 0.25,
        'proximity': 0.25,
        'verification': 0.20,
        'quantity_fit': 0.20,
        'delay_risk': 0.10,
    },
}

DEFAULT_WEIGHTS = WEIGHT_PROFILES['other']


def get_weights_for_type(need_type: str) -> dict:
    """Retrieve weights dictionary normalized to sum to 1.0 for given resource/need type."""
    weights = WEIGHT_PROFILES.get(need_type, DEFAULT_WEIGHTS).copy()
    total = sum(weights.values())
    if total > 0:
        return {k: v / total for k, v in weights.items()}
    return DEFAULT_WEIGHTS
