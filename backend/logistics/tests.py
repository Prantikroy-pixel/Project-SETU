from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Vehicle

User = get_user_model()


class LogisticsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.operator = User.objects.create_user(
            username="driver_rajesh",
            password="Password123!",
            role="transport_operator"
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="AS-01-XX-9999",
            vehicle_type="4x4 Relief Truck",
            operator=self.operator,
            status=Vehicle.STATUS_IDLE
        )

    def test_vehicle_list(self):
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vehicle_gps_ping(self):
        self.client.force_authenticate(user=self.operator)
        payload = {
            "latitude": 24.8333,
            "longitude": 92.7789,
            "status": "en_route"
        }
        response = self.client.post(f"/api/vehicles/{self.vehicle.id}/ping/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, "en_route")
        self.assertIsNotNone(self.vehicle.last_ping_at)
