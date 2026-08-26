"""
Tests for scoring algorithm in matching_engine.
"""

import unittest
from matching_engine.scoring import score_resources, score_single_resource, haversine_distance
from matching_engine.weights_config import get_weights_for_type, WEIGHT_PROFILES


class TestScoringEngine(unittest.TestCase):
    def setUp(self):
        self.need = {
            'id': 1,
            'type': 'medicine',
            'urgency': 'critical',
            'quantity': 100,
            'latitude': 24.8333,
            'longitude': 92.7789,
        }

        self.candidates = [
            {
                'id': 101,
                'type': 'medicine',
                'quantity_available': 120,
                'verification_status': 'verified_org',
                'latitude': 24.8400,  # ~1 km away
                'longitude': 92.7800,
            },
            {
                'id': 102,
                'type': 'medicine',
                'quantity_available': 40,
                'verification_status': 'unverified',
                'latitude': 25.1000,  # ~35 km away
                'longitude': 92.9000,
            },
            {
                'id': 103,
                'type': 'medicine',
                'quantity_available': 100,
                'verification_status': 'verified_org',
                'latitude': 25.8000,  # ~110 km away
                'longitude': 93.5000,
            }
        ]

    def test_haversine_distance(self):
        # Distance between Silchar (24.8333, 92.7789) and Guwahati (26.1445, 91.7362) is ~180-220 km
        dist = haversine_distance(24.8333, 92.7789, 26.1445, 91.7362)
        self.assertGreater(dist, 150)
        self.assertLess(dist, 250)

    def test_ranking_order(self):
        results = score_resources(self.need, self.candidates)
        self.assertEqual(len(results), 3)

        # Candidate 101 (close, verified, full quantity) should score highest
        self.assertEqual(results[0]['resource_id'], 101)
        self.assertGreater(results[0]['score'], results[1]['score'])
        self.assertGreater(results[1]['score'], results[2]['score'])

    def test_score_breakdown_keys(self):
        results = score_resources(self.need, self.candidates)
        first_breakdown = results[0]['score_breakdown']
        self.assertIn('urgency', first_breakdown)
        self.assertIn('proximity', first_breakdown)
        self.assertIn('verification', first_breakdown)
        self.assertIn('quantity_fit', first_breakdown)
        self.assertIn('delay_risk', first_breakdown)
        self.assertIn('distance_km', first_breakdown)

        # Critical urgency should give 1.0 urgency score
        self.assertEqual(first_breakdown['urgency'], 1.0)
        # Verified org should give 1.0 verification score
        self.assertEqual(first_breakdown['verification'], 1.0)

    def test_weights_profile(self):
        weights = get_weights_for_type('medicine')
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=4)
        self.assertGreater(weights['urgency'], 0.3)

    def test_delay_risk_penalty(self):
        weights = get_weights_for_type('medicine')
        cand_safe = {
            'id': 201,
            'type': 'medicine',
            'quantity_available': 100,
            'verification_status': 'verified_org',
            'latitude': 24.8400,
            'longitude': 92.7800,
            'condition_risk': 0.0,
        }
        cand_hazardous = {
            'id': 202,
            'type': 'medicine',
            'quantity_available': 100,
            'verification_status': 'verified_org',
            'latitude': 24.8400,
            'longitude': 92.7800,
            'condition_risk': 0.85,  # High risk along corridor
        }

        score_safe = score_single_resource(self.need, cand_safe, weights)
        score_hazard = score_single_resource(self.need, cand_hazardous, weights)

        self.assertGreater(score_safe['score'], score_hazard['score'])
        self.assertEqual(score_safe['score_breakdown']['delay_risk'], 1.0)
        self.assertEqual(score_hazard['score_breakdown']['delay_risk'], 0.15)


if __name__ == '__main__':
    unittest.main()
