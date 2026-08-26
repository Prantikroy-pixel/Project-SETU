from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import District

User = get_user_model()


class AccountsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.district = District.objects.create(
            name="Cachar",
            state="Assam",
            population=1736000
        )

    def test_user_registration(self):
        payload = {
            "username": "citizen_user_1",
            "password": "Password123!",
            "email": "citizen1@setu.org",
            "role": "citizen",
            "phone_number": "+919876543210",
            "preferred_language": "en",
            "district_id": self.district.id
        }
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "citizen")
        self.assertEqual(response.data["user"]["district"], self.district.id)

    def test_user_login_jwt(self):
        user = User.objects.create_user(
            username="admin_user",
            password="Password123!",
            role="district_admin"
        )
        payload = {
            "username": "admin_user",
            "password": "Password123!"
        }
        response = self.client.post("/api/auth/login/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "admin_user")

    def test_me_endpoint_authenticated(self):
        user = User.objects.create_user(
            username="transport_user",
            password="Password123!",
            role="transport_operator"
        )
        self.client.force_authenticate(user=user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "transport_operator")
