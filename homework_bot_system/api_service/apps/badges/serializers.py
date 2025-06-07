from rest_framework import serializers
from django.utils import timezone
from .models import Badge, UserBadge, Competition, CompetitionParticipant
from apps.users.serializers import UserProfileSerializer


class BadgeSerializer(serializers.ModelSerializer):
    """مسلسل الشارات"""
    
    earned_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Badge
        fields = [
            'id', 'name', 'description', 'icon', 'badge_type', 'rarity',
            'points_required', 'streak_required', 'is_active',
            'earned_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_earned_count(self, obj):
        """عدد المستخدمين الذين حصلوا على الشارة"""
        return obj.userbadge_set.count()


class UserBadgeSerializer(serializers.ModelSerializer):
    """مسلسل شارات المستخدم"""
    
    badge = BadgeSerializer(read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = UserBadge
        fields = ['id', 'user', 'user_name', 'badge', 'earned_at']
        read_only_fields = ['id', 'user', 'earned_at']


class CompetitionSerializer(serializers.ModelSerializer):
    """مسلسل المسابقات"""
    
    participants_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Competition
        fields = [
            'id', 'title', 'description', 'competition_type', 'status',
            'start_date', 'end_date', 'max_participants', 'prize_points',
            'participants_count', 'is_active', 'time_remaining',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_participants_count(self, obj):
        """عدد المشاركين"""
        return obj.participants.count()
    
    def get_is_active(self, obj):
        """هل المسابقة نشطة"""
        now = timezone.now()
        return obj.start_date <= now <= obj.end_date
    
    def get_time_remaining(self, obj):
        """الوقت المتبقي"""
        now = timezone.now()
        if now < obj.start_date:
            time_diff = obj.start_date - now
            return f"تبدأ خلال {time_diff.days} يوم"
        elif now <= obj.end_date:
            time_diff = obj.end_date - now
            return f"تنتهي خلال {time_diff.days} يوم"
        return "انتهت"


class CompetitionParticipantSerializer(serializers.ModelSerializer):
    """مسلسل مشاركي المسابقة"""
    
    user = UserProfileSerializer(read_only=True)
    competition_title = serializers.CharField(source='competition.title', read_only=True)
    
    class Meta:
        model = CompetitionParticipant
        fields = [
            'id', 'user', 'competition', 'competition_title',
            'points_earned', 'rank', 'joined_at'
        ]
        read_only_fields = ['id', 'user', 'points_earned', 'rank', 'joined_at']


class CompetitionDetailSerializer(CompetitionSerializer):
    """مسلسل تفاصيل المسابقة"""
    
    participants = CompetitionParticipantSerializer(many=True, read_only=True)
    top_participants = serializers.SerializerMethodField()
    
    class Meta(CompetitionSerializer.Meta):
        fields = CompetitionSerializer.Meta.fields + ['participants', 'top_participants']
    
    def get_top_participants(self, obj):
        """أفضل 10 مشاركين"""
        top_participants = obj.participants.order_by('-points_earned')[:10]
        return CompetitionParticipantSerializer(top_participants, many=True).data


class BadgeStatisticsSerializer(serializers.Serializer):
    """مسلسل إحصائيات الشارات"""
    
    total_badges = serializers.IntegerField()
    earned_badges = serializers.IntegerField()
    common_badges = serializers.IntegerField()
    rare_badges = serializers.IntegerField()
    epic_badges = serializers.IntegerField()
    legendary_badges = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)