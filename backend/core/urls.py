"""
URL router configuration for core app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DistrictViewSet, NeedViewSet, ResourceViewSet,
    ConditionViewSet, AllocationViewSet, AlertViewSet,
    InstitutionViewSet, BorderBoundaryView, BorderProximityView,
    RouteBorderAnalysisView, DistrictBoundaryView, StateBoundaryView,
    SyncDistrictBoundariesView
)

app_name = 'core'

router = DefaultRouter()
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'needs', NeedViewSet, basename='need')
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'conditions', ConditionViewSet, basename='condition')
router.register(r'allocations', AllocationViewSet, basename='allocation')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'institutions', InstitutionViewSet, basename='institution')

urlpatterns = [
    # Administrative, Interstate & International Boundary Tracking APIs
    path('boundaries/district-boundary/', DistrictBoundaryView.as_view(), name='district-boundary'),
    path('boundaries/state-boundary/', StateBoundaryView.as_view(), name='state-boundary'),
    path('boundaries/sync-districts/', SyncDistrictBoundariesView.as_view(), name='sync-district-boundaries'),
    path('boundaries/ner-borders/', BorderBoundaryView.as_view(), name='ner-borders'),
    path('boundaries/check-proximity/', BorderProximityView.as_view(), name='border-proximity'),
    path('boundaries/analyze-route/', RouteBorderAnalysisView.as_view(), name='border-route-analysis'),
    path('', include(router.urls)),
]
