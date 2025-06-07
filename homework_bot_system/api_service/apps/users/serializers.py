from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User
from apps.sections.models import Section

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)
    rank_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'telegram_id', 'full_name', 'username', 'email',
            'section', 'section_name', 'role', 'personality', 'points',
            'penalty_counter', 'excellence_points', 'submission_streak',
            'is_muted', 'profile_photo_url', 'last_activity', 'status',
            'rank_title', 'date_joined'
        ]
        read_only_fields = ['telegram_id', 'points', 'penalty_counter', 
                           'excellence_points', 'submission_streak', 'last_activity']

class UserProfileSerializer(serializers.ModelSerializer):
    section_name = serializers.CharField(source='section.name', read_only=True)
    rank_title = serializers.CharField(read_only=True)
    total_submissions = serializers.IntegerField(read_only=True)
    approved_submissions = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'username', 'email', 'section_name',
            'personality', 'points', 'excellence_points', 'submission_streak',
            'profile_photo_url', 'rank_title', 'total_submissions',
            'approved_submissions', 'date_joined', 'last_activity'
        ]
        read_only_fields = ['points', 'excellence_points', 'submission_streak']

class ChangePersonalitySerializer(serializers.Serializer):
    personality = serializers.ChoiceField(choices=User.Personality.choices)
    
    def update(self, instance, validated_data):
        instance.personality = validated_data['personality']
        instance.save()
        return instance

class UserRankingSerializer(serializers.ModelSerializer):
    rank = serializers.IntegerField(read_only=True)
    section_name = serializers.CharField(source='section.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'username', 'section_name', 'points',
            'excellence_points', 'submission_streak', 'rank'
        ]