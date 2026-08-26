"""
URL router configuration for logistics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet

app_name = 'logistics'

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')

urlpatterns = [
    path('', include(router.urls)),
]
