"""
Matching Engine Package for SETU
Provides multi-criteria candidate resource scoring and AI disruption-risk prediction.
"""

from .scoring import score_resources
from .weights_config import WEIGHT_PROFILES, DEFAULT_WEIGHTS

__all__ = ['score_resources', 'WEIGHT_PROFILES', 'DEFAULT_WEIGHTS']
