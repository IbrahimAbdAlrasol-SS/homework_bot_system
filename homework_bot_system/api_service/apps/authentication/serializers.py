from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from apps.users.models import User
from core.jwt_auth import JWTAuthentication

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Serializer لتسجيل الدخول"""
    
    telegram_id = serializers.IntegerField(
        help_text="معرف التلكرام الفريد"
    )
    
    def validate(self, attrs):
        telegram_id = attrs.get('telegram_id')
        
        if not telegram_id:
            raise serializers.ValidationError("معرف التلكرام مطلوب")
        
        try:
            user = User.objects.get(
                telegram_id=telegram_id,
                status='active'
            )
        except User.DoesNotExist:
            raise serializers.ValidationError("المستخدم غير موجود أو غير نشط")
        
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        user = validated_data['user']
        
        # إنشاء رموز JWT
        access_token, refresh_token = JWTAuthentication.generate_tokens(user)
        
        # تحديث آخر نشاط
        user.update_activity()
        
        return {
            'user': user,
            'access_token': access_token,
            'refresh_token': refresh_token
        }


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer لتحديث الرمز"""
    
    refresh_token = serializers.CharField(
        help_text="رمز التحديث"
    )
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh_token')
        
        if not refresh_token:
            raise serializers.ValidationError("رمز التحديث مطلوب")
        
        # التحقق من صحة رمز التحديث
        user = JWTAuthentication.verify_token(refresh_token, 'refresh')
        if not user:
            raise serializers.ValidationError("رمز التحديث غير صحيح أو منتهي الصلاحية")
        
        attrs['user'] = user
        return attrs
    
    def create(self, validated_data):
        user = validated_data['user']
        
        # إنشاء رمز وصول جديد
        access_token, _ = JWTAuthentication.generate_tokens(user)
        
        return {
            'access_token': access_token,
            'user': user
        }


class LogoutSerializer(serializers.Serializer):
    """Serializer لتسجيل الخروج"""
    
    refresh_token = serializers.CharField(
        required=False,
        help_text="رمز التحديث (اختياري)"
    )
    
    def validate(self, attrs):
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer لملف المستخدم"""
    
    rank_title = serializers.ReadOnlyField()
    is_admin = serializers.ReadOnlyField()
    is_student = serializers.ReadOnlyField()
    section_name = serializers.CharField(source='section.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'telegram_id', 'first_name', 'last_name',
            'username', 'email', 'section', 'section_name',
            'role', 'personality', 'points', 'penalty_counter',
            'excellence_points', 'submission_streak', 'is_muted',
            'profile_photo_url', 'last_activity', 'status',
            'rank_title', 'is_admin', 'is_student'
        ]
        read_only_fields = [
            'id', 'telegram_id', 'points', 'penalty_counter',
            'excellence_points', 'submission_streak', 'is_muted',
            'last_activity', 'status'
        ]