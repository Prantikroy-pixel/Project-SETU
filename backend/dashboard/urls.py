"""
URL routing for dashboard analytics app.
"""

from django.urls import path
from .views import DistrictSummaryView

app_name = 'dashboard'

urlpatterns = [
    path('district-summary/', DistrictSummaryView.as_view(), name='district_summary'),
]
