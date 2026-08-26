from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import District, Need, Resource, Allocation
from logistics.models import Vehicle
from .models import Match
from core.spatial_compat import HAS_GIS

if HAS_GIS:
    from django.contrib.gis.geos import Point
else:
    from core.spatial_compat import MockPoint as Point

User = get_user_model()


class MatchingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="ngo_provider",
            password="Password123!",
            role="ngo",
            is_verified=True
        )
        self.district = District.objects.create(name="Cachar", state="Assam")

        self.need = Need.objects.create(
            type="food",
            urgency="high",
            quantity=100,
            unit="packets",
            location=Point(92.7789, 24.8333),
            district=self.district,
            reported_by=self.user,
            status="open"
        )

        self.resource1 = Resource.objects.create(
            type="food",
            quantity_available=150,
            unit="packets",
            location=Point(92.7800, 24.8350),  # very close
            district=self.district,
            provider=self.user,
            verification_status="verified_org"
        )

        self.resource2 = Resource.objects.create(
            type="food",
            quantity_available=50,
            unit="packets",
            location=Point(93.5000, 25.5000),  # far away
            district=self.district,
            provider=self.user,
            verification_status="unverified"
        )

        self.vehicle = Vehicle.objects.create(
            registration_number="AS-11-AA-1111",
            vehicle_type="Mini Van",
            operator=self.user,
            status="idle"
        )

    def test_get_matches_for_need(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/needs/{self.need.id}/matches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("matches", response.data)
        matches = response.data["matches"]
        self.assertEqual(len(matches), 2)

        # Resource 1 (closer, verified, full capacity) should rank first with higher score
        self.assertEqual(matches[0]["resource"], self.resource1.id)
        self.assertGreater(matches[0]["score"], matches[1]["score"])
        self.assertIn("score_breakdown", matches[0])

    def test_confirm_match_creates_allocation(self):
        admin_user = User.objects.create_user(
            username="admin_matcher",
            password="Password123!",
            role="district_admin",
            is_staff=True
        )
        self.client.force_authenticate(user=admin_user)
        # First trigger matches
        self.client.get(f"/api/needs/{self.need.id}/matches/")
        match_obj = Match.objects.filter(need=self.need, resource=self.resource1).first()
        self.assertIsNotNone(match_obj)

        payload = {"vehicle_id": self.vehicle.id}
        response = self.client.post(f"/api/matches/{match_obj.id}/confirm/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("allocation", response.data)

        # Verify DB updates
        match_obj.refresh_from_db()
        self.assertEqual(match_obj.status, Match.STATUS_CONFIRMED)

        self.need.refresh_from_db()
        self.assertEqual(self.need.status, "matched")

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.STATUS_EN_ROUTE)

        allocation = Allocation.objects.get(match=match_obj)
        self.assertEqual(allocation.vehicle, self.vehicle)
        self.assertIsNotNone(allocation.route_geojson)
