"""
Views for accounts app.
Provides user registration, JWT login, profile inspection, and user directory endpoints.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, AdminUserCreateSerializer
)
from .permissions import IsDistrictAdmin

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Register a new user account (Citizen or NGO). Field officers and operators are blocked.
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for instant login upon registration
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.username
        refresh['role'] = user.role
        refresh['district_id'] = user.district_id
        refresh['is_verified'] = user.is_verified

        return Response({
            'message': 'User successfully registered.',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class AdminCreateUserView(generics.CreateAPIView):
    """
    POST /api/auth/admin/create-user/
    Allows District and Central Administrators to register Field Officers, Transport Operators, and Verified NGOs.
    """
    queryset = User.objects.all()
    serializer_class = AdminUserCreateSerializer
    permission_classes = [IsDistrictAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'message': f"Account for {user.get_role_display()} '{user.username}' created successfully.",
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class VerifyUserView(APIView):
    """
    POST /api/auth/users/<pk>/verify/
    Verify or approve a pending NGO or provider account.
    """
    permission_classes = [IsDistrictAdmin]

    def post(self, request, pk):
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_verified = request.data.get('is_verified', True)
        target_user.is_verified = bool(is_verified)
        target_user.save(update_fields=['is_verified'])

        return Response({
            'message': f"User '{target_user.username}' verification status updated to {target_user.is_verified}.",
            'user': UserSerializer(target_user).data
        }, status=status.HTTP_200_OK)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Authenticate user with credentials and return JWT tokens + profile object.
    """
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """
    GET /api/auth/me/
    PATCH /api/auth/me/
    Get or update current authenticated user profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    """
    GET /api/auth/users/?role=&district=&is_verified=
    List users with optional role, district, or verification status filtering.
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get('role')
        district = self.request.query_params.get('district')
        is_verified = self.request.query_params.get('is_verified')
        
        if role:
            qs = qs.filter(role=role)
        if district:
            qs = qs.filter(district_id=district)
        if is_verified is not None:
            verified_bool = is_verified.lower() in ['true', '1', 'yes']
            qs = qs.filter(is_verified=verified_bool)
            
        return qs
