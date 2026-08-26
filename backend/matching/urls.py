"""
URL routing for matching app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchViewSet, NeedMatchesView, MatchConfirmStandaloneView

app_name = 'matching'

router = DefaultRouter()
router.register(r'matches', MatchViewSet, basename='match')

urlpatterns = [
    path('needs/<int:need_id>/matches/', NeedMatchesView.as_view(), name='need_matches'),
    path('matches/<int:match_id>/confirm/', MatchConfirmStandaloneView.as_view(), name='match_confirm_standalone'),
    path('', include(router.urls)),
]
