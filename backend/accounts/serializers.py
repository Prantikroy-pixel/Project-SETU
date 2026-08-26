"""
Serializers for accounts app.
Handles User registration, user profile serialization, and custom JWT tokens.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from core.models import District

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    district_state = serializers.CharField(source='district.state', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'preferred_language',
            'district',
            'district_name',
            'district_state',
            'is_verified',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source='district',
        required=False,
        allow_null=True
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'preferred_language',
            'district_id',
            'is_verified',
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']
        extra_kwargs = {
            'email': {'required': False},
            'phone_number': {'required': False},
            'role': {'required': False},
        }

    def validate_role(self, value):
        # Public self-registration only allows citizen and ngo. Administrative and officer roles are strictly prohibited.
        if value not in [User.ROLE_CITIZEN, User.ROLE_NGO]:
            raise serializers.ValidationError(
                "Privilege Escalation Blocked: Public registration is only permitted for Citizens and NGOs. "
                "Field Officers, Transport Operators, and Administrators must be provisioned directly by an Administrator."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', User.ROLE_CITIZEN)
        
        # Strip any client-supplied administrative or verification flags
        validated_data.pop('is_verified', None)
        validated_data.pop('is_staff', None)
        validated_data.pop('is_superuser', None)
        
        # NGOs start unverified pending admin approval; Citizens are non-administrative users
        validated_data['is_verified'] = False
        validated_data['role'] = role

        user = User(**validated_data)
        user.set_password(password)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        return user


class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source='district',
        required=False,
        allow_null=True
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
            'phone_number',
            'preferred_language',
            'district_id',
            'is_verified',
        ]
        extra_kwargs = {
            'email': {'required': False},
            'phone_number': {'required': False},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.get('role', User.ROLE_FIELD_OFFICER)
        
        # When created by Admin, officers and operators are verified by default
        if 'is_verified' not in validated_data:
            validated_data['is_verified'] = True
            
        if role in [User.ROLE_ADMIN, User.ROLE_DISTRICT_ADMIN]:
            validated_data['is_staff'] = True

        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Augments standard JWT token response with user profile details."""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        token['district_id'] = user.district_id
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
