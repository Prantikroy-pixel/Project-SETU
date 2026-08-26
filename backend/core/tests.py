from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import District, Need, Resource, Condition, Alert
from .spatial_compat import HAS_GIS

if HAS_GIS:
    from django.contrib.gis.geos import Point
else:
    from .spatial_compat import MockPoint as Point

User = get_user_model()


class CoreAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="tester",
            password="Password123!",
            role="field_officer"
        )
        self.district = District.objects.create(
            name="Kamrup",
            state="Assam",
            population=1500000
        )
        self.client.force_authenticate(user=self.user)

    def test_create_and_list_district(self):
        response = self.client.get("/api/districts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"] if "results" in response.data else response.data), 1)

    def test_report_need(self):
        payload = {
            "type": "medicine",
            "urgency": "critical",
            "quantity": 250,
            "unit": "packets",
            "description": "Urgent ORS and antibiotics needed at flood shelter",
            "latitude": 26.1445,
            "longitude": 91.7362,
            "district": self.district.id
        }
        response = self.client.post("/api/needs/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["type"], "medicine")
        self.assertEqual(response.data["quantity"], 250)
        self.assertIsNotNone(response.data["location"])
        self.assertEqual(response.data["location"]["latitude"], 26.1445)

    def test_register_resource(self):
        ngo_user = User.objects.create_user(
            username="ngo_resource_provider",
            password="Password123!",
            role="ngo",
            is_verified=True
        )
        self.client.force_authenticate(user=ngo_user)
        payload = {
            "type": "medicine",
            "quantity_available": 500,
            "unit": "packets",
            "verification_status": "verified_org",
            "latitude": 26.1500,
            "longitude": 91.7400,
            "district": self.district.id
        }
        response = self.client.post("/api/resources/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity_available"], 500)

    def test_report_condition_triggers_alert(self):
        payload = {
            "condition_type": "road_status",
            "value": "blocked",
            "latitude": 26.1400,
            "longitude": 91.7300,
            "district": self.district.id,
            "source": "field_report"
        }
        response = self.client.post("/api/conditions/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify automated alert creation
        alerts = Alert.objects.filter(district=self.district, alert_type="road_blocked")
        self.assertTrue(alerts.exists())
        self.assertEqual(alerts.first().severity, "critical")

    def test_predict_risk_endpoint(self):
        response = self.client.get("/api/conditions/predict-risk/?lat=25.5&lon=91.8&rainfall=110&slope=32")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("risk_score", response.data)
        self.assertIn("risk_level", response.data)
        self.assertGreater(response.data["risk_score"], 0.0)

    def test_district_unauthenticated_http_methods_security(self):
        anon_client = APIClient()

        # 1. GET /api/districts/{id}/ -> 200 OK (Public read-only by design for disaster coordination)
        get_res = anon_client.get(f"/api/districts/{self.district.id}/")
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)

        # 2. POST /api/districts/{id}/ -> 401 Unauthorized (Blocked by IsAdminUserOrReadOnly before method routing)
        post_res = anon_client.post(f"/api/districts/{self.district.id}/", {"name": "Hacked"}, format="json")
        self.assertIn(post_res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_405_METHOD_NOT_ALLOWED])

        # 3. PUT /api/districts/{id}/ -> 401 Unauthorized (Blocked by IsAdminUserOrReadOnly)
        put_res = anon_client.put(f"/api/districts/{self.district.id}/", {"name": "Hacked", "state": "Assam", "population": 100}, format="json")
        self.assertEqual(put_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # 4. PATCH /api/districts/{id}/ -> 401 Unauthorized (Blocked by IsAdminUserOrReadOnly)
        patch_res = anon_client.patch(f"/api/districts/{self.district.id}/", {"name": "Hacked"}, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_401_UNAUTHORIZED)

        # 5. DELETE /api/districts/{id}/ -> 401 Unauthorized (Blocked by IsAdminUserOrReadOnly)
        delete_res = anon_client.delete(f"/api/districts/{self.district.id}/")
        self.assertEqual(delete_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_district_non_admin_forbidden(self):
        # A citizen user trying to modify a district
        citizen_user = User.objects.create_user(
            username="regular_citizen",
            password="Password123!",
            role="citizen"
        )
        self.client.force_authenticate(user=citizen_user)

        # PUT -> 403 Forbidden
        put_res = self.client.put(f"/api/districts/{self.district.id}/", {"name": "Hacked", "state": "Assam", "population": 100}, format="json")
        self.assertEqual(put_res.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE -> 403 Forbidden
        delete_res = self.client.delete(f"/api/districts/{self.district.id}/")
        self.assertEqual(delete_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_district_admin_authorized(self):
        # An admin user modifying a district
        admin_user = User.objects.create_user(
            username="ddma_admin",
            password="Password123!",
            role="district_admin"
        )
        self.client.force_authenticate(user=admin_user)

        # PATCH -> 200 OK
        patch_res = self.client.patch(f"/api/districts/{self.district.id}/", {"population": 1600000}, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.district.refresh_from_db()
        self.assertEqual(self.district.population, 1600000)
