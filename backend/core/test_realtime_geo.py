"""
Unit and Integration Tests for Real-Time Institution and Boundary Fetchers.
"""

import os
import sys
import unittest

# Ensure backend and project root are in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.boundary_service import RealtimeBoundaryFetcher, BorderTrackingService, NER_BORDER_CHECKPOINTS
from core.institution_service import InstitutionIngestionService, MASTER_NER_INSTITUTIONS


class TestRealtimeGeoFetchers(unittest.TestCase):

    def setUp(self):
        self.boundary_fetcher = RealtimeBoundaryFetcher(timeout_sec=8)
        self.institution_service = InstitutionIngestionService(timeout_sec=10)
        self.border_service = BorderTrackingService(timeout_sec=8)

    def test_live_district_boundary_fetch(self):
        """Test live extraction of official GeoJSON polygon for a district."""
        result = self.boundary_fetcher.fetch_district_geojson_boundary("Kamrup Metropolitan", "Assam")
        self.assertIsNotNone(result, "Should retrieve boundary data for Kamrup Metropolitan")
        self.assertIn("geometry", result)
        self.assertIn(result["geometry"]["type"], ["Polygon", "MultiPolygon"])
        self.assertGreater(len(result["geometry"]["coordinates"]), 0)
        self.assertEqual(result["district_name"], "Kamrup Metropolitan")

    def test_live_state_boundary_fetch(self):
        """Test live extraction of official GeoJSON polygon for a state."""
        result = self.boundary_fetcher.fetch_state_geojson_boundary("Assam")
        self.assertIsNotNone(result, "Should retrieve boundary data for Assam")
        self.assertIn("geometry", result)
        self.assertIn(result["geometry"]["type"], ["Polygon", "MultiPolygon"])
        self.assertEqual(result["state_name"], "Assam")

    def test_boundary_caching(self):
        """Test that repeated boundary queries retrieve from cache instantly."""
        res1 = self.boundary_fetcher.fetch_district_geojson_boundary("Cachar", "Assam")
        res2 = self.boundary_fetcher.fetch_district_geojson_boundary("Cachar", "Assam")
        if res1 and res2:
            self.assertEqual(res1["geometry"]["type"], res2["geometry"]["type"])

    def test_live_osm_institutions_fetch(self):
        """Test live Overpass querying for hospitals and public institutions."""
        # Query Guwahati bounding box
        bbox = (26.10, 91.70, 26.20, 91.80)
        institutions = self.institution_service.fetch_live_osm_institutions(bbox=bbox, limit=15)
        self.assertIsInstance(institutions, list)
        self.assertGreater(len(institutions), 0, "Should fetch live institutions in Guwahati area")

        first = institutions[0]
        self.assertIn("name", first)
        self.assertIn("category", first)
        self.assertIn("lat", first)
        self.assertIn("lon", first)
        self.assertEqual(first["source_api"], "openstreetmap_overpass_live")

    def test_district_scoped_institution_fetch(self):
        """Test querying live institutions for a specific named district."""
        institutions = self.institution_service.fetch_live_institutions_for_district("Cachar", "Assam")
        self.assertIsInstance(institutions, list)

    def test_border_proximity_analysis(self):
        """Test border geofencing and proximity calculations."""
        # Dawki coordinate (Meghalaya-Bangladesh border)
        dawki_lat, dawki_lon = 25.1842, 92.0286
        proximity = self.border_service.check_point_border_proximity(dawki_lat, dawki_lon, threshold_km=10.0)

        self.assertTrue(proximity["is_near_border"])
        self.assertLess(proximity["distance_to_nearest_checkpoint_km"], 1.0)
        self.assertEqual(proximity["border_type"], "international_border")
        self.assertTrue(proximity["requires_international_clearance"])

    def test_route_border_crossing_detection(self):
        """Test route analysis detecting interstate / international checkposts."""
        route = [
            {"lat": 26.1445, "lon": 91.7362},  # Guwahati
            {"lat": 26.0964, "lon": 91.8683},  # Jorabat Checkpost
            {"lat": 25.5788, "lon": 91.8933},  # Shillong
        ]
        analysis = self.border_service.analyze_route_crossings(route)
        self.assertGreaterEqual(analysis["total_border_checkpoints_on_route"], 1)
        self.assertGreaterEqual(analysis["interstate_crossings"], 1)


if __name__ == '__main__':
    unittest.main()
