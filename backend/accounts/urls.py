"""
URL routing for accounts app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, MeView, UserListView, AdminCreateUserView, VerifyUserView
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('admin/create-user/', AdminCreateUserView.as_view(), name='admin_create_user'),
    path('users/<int:pk>/verify/', VerifyUserView.as_view(), name='verify_user'),
]
