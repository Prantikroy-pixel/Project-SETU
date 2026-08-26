from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import District, Need, Resource, Condition
from core.spatial_compat import HAS_GIS

if HAS_GIS:
    from django.contrib.gis.geos import Point
else:
    from core.spatial_compat import MockPoint as Point

User = get_user_model()


class DashboardAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst",
            password="Password123!",
            role="district_admin"
        )
        self.dist1 = District.objects.create(name="Cachar", state="Assam", population=1700000)
        self.dist2 = District.objects.create(name="East Khasi Hills", state="Meghalaya", population=825000)

        # Cachar has critical needs and a blocked road
        Need.objects.create(
            type="medicine",
            urgency="critical",
            quantity=200,
            unit="units",
            location=Point(92.78, 24.83),
            district=self.dist1,
            reported_by=self.user,
            status="open"
        )
        Condition.objects.create(
            condition_type="road_status",
            value="blocked",
            location=Point(92.78, 24.83),
            district=self.dist1,
            reported_by=self.user
        )

        # East Khasi Hills has available resources
        Resource.objects.create(
            type="food",
            quantity_available=1000,
            unit="kg",
            location=Point(91.89, 25.57),
            district=self.dist2,
            provider=self.user,
            verification_status="verified_org"
        )

    def test_district_summary_aggregation(self):
        response = self.client.get("/api/dashboard/district-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("overview", response.data)
        self.assertIn("districts", response.data)

        overview = response.data["overview"]
        self.assertEqual(overview["total_districts_monitored"], 2)
        self.assertEqual(overview["total_open_needs"], 1)
        self.assertEqual(overview["total_critical_needs"], 1)
        self.assertEqual(overview["total_blocked_corridors"], 1)

        districts = response.data["districts"]
        # Cachar with critical need & blocked road should rank higher in bottleneck index
        self.assertEqual(districts[0]["name"], "Cachar")
        self.assertGreater(districts[0]["bottleneck_index"], districts[1]["bottleneck_index"])
        self.assertEqual(districts[0]["hazards"]["blocked_roads_count"], 1)
