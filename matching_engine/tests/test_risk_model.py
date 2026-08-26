"""
Tests for ML risk model and Realtime Hazard Fetcher integration in matching_engine.
"""

import unittest
from matching_engine.risk_model.predict import (
    predict_risk,
    fetch_realtime_features_for_coord,
    _heuristic_risk
)
from matching_engine.risk_model.train import (
    assemble_unified_training_dataset,
    train_and_save_model,
    FEATURE_NAMES
)


class TestRiskModel(unittest.TestCase):
    def test_predict_risk_structure(self):
        result = predict_risk(lat=24.8333, lon=92.7789, rainfall=120.0, slope=35.0)
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('is_critical', result)
        self.assertIn('is_realtime_fetched', result)
        self.assertIn('explanation', result)
        self.assertIn('features', result)

        self.assertGreaterEqual(result['risk_score'], 0.0)
        self.assertLessEqual(result['risk_score'], 1.0)
        self.assertIn(result['risk_level'], ['low', 'medium', 'high', 'critical'])

        # Check features dictionary
        features = result['features']
        self.assertIn('rainfall_mm', features)
        self.assertIn('slope_degrees', features)
        self.assertIn('elevation_m', features)
        self.assertIn('soil_saturation', features)
        self.assertIn('drainage_quality', features)
        self.assertIn('vegetation_cover', features)

    def test_high_hazard_vs_low_hazard(self):
        # Extreme rain and steep slope
        high_risk = predict_risk(lat=25.5, lon=91.8, rainfall=180.0, slope=45.0, soil_saturation=0.95)
        # Gentle rain, flat terrain
        low_risk = predict_risk(lat=25.5, lon=91.8, rainfall=5.0, slope=2.0, soil_saturation=0.2)

        self.assertGreater(high_risk['risk_score'], low_risk['risk_score'])
        self.assertTrue(high_risk['risk_level'] in ['high', 'critical'])
        self.assertTrue(low_risk['risk_level'] in ['low', 'medium'])

    def test_realtime_feature_fetching(self):
        # Query Silchar coordinate with live real-time enabled
        result = predict_risk(lat=24.8333, lon=92.7789, use_realtime=True)
        self.assertIsNotNone(result['risk_score'])
        self.assertIn('rainfall_mm', result['features'])
        self.assertIn('slope_degrees', result['features'])
        self.assertIn('elevation_m', result['features'])
        self.assertGreaterEqual(result['features']['rainfall_mm'], 0.0)

    def test_coordinate_caching(self):
        # First call fetches/computes
        features1, _ = fetch_realtime_features_for_coord(26.1445, 91.7362)
        # Second call should retrieve from cache
        features2, cached = fetch_realtime_features_for_coord(26.1445, 91.7362)
        self.assertEqual(features1['elevation'], features2['elevation'])
        self.assertTrue(cached)

    def test_heuristic_fallback(self):
        prob = _heuristic_risk(
            rainfall=150.0,
            slope=35.0,
            elevation=800.0,
            soil_saturation=0.9,
            drainage_quality=1.5,
            vegetation_cover=0.3
        )
        self.assertGreaterEqual(prob, 0.7)

    def test_predict_route_risk_corridor(self):
        from matching_engine.risk_model.predict import predict_route_risk, interpolate_route_waypoints, detect_route_anomalies
        
        # Define 4-point corridor: Shillong to Silchar
        waypoints = [
            [25.5788, 91.8933],
            [25.4500, 92.2000],
            [25.1812, 93.0175],
            [24.8333, 92.7789]
        ]
        
        route_res = predict_route_risk(waypoints=waypoints, use_realtime=True)
        self.assertIn('route_composite_risk', route_res)
        self.assertIn('threat_level', route_res)
        self.assertIn('corridor_status', route_res)
        self.assertIn('range_metrics', route_res)
        self.assertIn('hazard_subranges', route_res)
        self.assertIn('waypoint_analysis', route_res)
        self.assertGreaterEqual(route_res['route_composite_risk'], 0.0)
        self.assertLessEqual(route_res['route_composite_risk'], 1.0)
        self.assertGreater(route_res['total_distance_km'], 50.0)

    def test_interpolate_route_waypoints(self):
        from matching_engine.risk_model.predict import interpolate_route_waypoints
        pts = [[25.5, 91.8], [24.8, 92.7]]
        interpolated = interpolate_route_waypoints(pts, max_samples=6)
        self.assertGreaterEqual(len(interpolated), 2)
        self.assertLessEqual(len(interpolated), 6)
        self.assertEqual(interpolated[0][0], 25.5)
        self.assertEqual(interpolated[-1][0], 24.8)

    def test_detect_route_anomalies(self):
        from matching_engine.risk_model.predict import detect_route_anomalies
        mock_waypoint_results = [
            {
                'latitude': 25.5, 'longitude': 91.8, 'distance_along_route_km': 0.0,
                'risk_score': 0.3,
                'features': {'rainfall_mm': 15.0, 'slope_degrees': 5.0, 'soil_saturation': 0.3, 'drainage_quality': 1.2}
            },
            {
                'latitude': 25.2, 'longitude': 92.1, 'distance_along_route_km': 60.0,
                'risk_score': 0.85,
                'features': {'rainfall_mm': 85.0, 'slope_degrees': 28.0, 'soil_saturation': 0.88, 'drainage_quality': 2.8}
            }
        ]
        anomalies = detect_route_anomalies(mock_waypoint_results)
        self.assertGreater(len(anomalies), 0)
        types = [a['type'] for a in anomalies]
        self.assertTrue('landslide_threat' in types or 'rainfall_surge_anomaly' in types)

    def test_dataset_assembly_structure(self):
        X, y, counts = assemble_unified_training_dataset(fetch_live=False, n_augmented=50)
        self.assertEqual(X.shape[1], 6)
        self.assertEqual(len(X), len(y))
        self.assertGreater(counts['total'], 0)
        self.assertIn('historical', counts)
        self.assertIn('augmented', counts)


if __name__ == '__main__':
    unittest.main()
