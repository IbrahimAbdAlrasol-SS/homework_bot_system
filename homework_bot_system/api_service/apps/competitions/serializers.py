from rest_framework import serializers
from django.utils import timezone
from .models import (
    Competition, CompetitionParticipant, SectionCompetition,
    CompetitionRound, CompetitionVote, CompetitionReward
)
from apps.users.serializers import UserBasicSerializer
from apps.sections.serializers import SectionBasicSerializer
from apps.badges.serializers import BadgeSerializer

class CompetitionSerializer(serializers.ModelSerializer):
    """مسلسل المسابقة الأساسي"""
    
    competition_type_display = serializers.CharField(source='get_competition_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    participant_count = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Competition
        fields = [
            'id', 'title', 'description', 'competition_type', 'competition_type_display',
            'period', 'period_display', 'status', 'status_display',
            'start_date', 'end_date', 'max_participants', 'participant_count',
            'early_submission_points', 'on_time_points', 'late_penalty',
            'prize_structure', 'auto_ranking', 'allow_voting', 'is_featured',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """التحقق من صحة البيانات"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
        
        if data.get('start_date') and data['start_date'] < timezone.now():
            if not self.instance:  # إنشاء جديد
                raise serializers.ValidationError("لا يمكن إنشاء مسابقة بتاريخ بداية في الماضي")
        
        return data

class CompetitionParticipantSerializer(serializers.ModelSerializer):
    """مسلسل مشاركين المسابقة"""
    
    user = UserBasicSerializer(read_only=True)
    competition_title = serializers.CharField(source='competition.title', read_only=True)
    rank_change = serializers.SerializerMethodField()
    
    class Meta:
        model = CompetitionParticipant
        fields = [
            'id', 'user', 'competition', 'competition_title',
            'total_score', 'submission_score', 'badge_score', 'bonus_score',
            'rank', 'previous_rank', 'rank_change',
            'submissions_count', 'early_submissions', 'late_submissions',
            'joined_at', 'last_activity'
        ]
        read_only_fields = ['joined_at', 'last_activity']
    
    def get_rank_change(self, obj):
        """حساب تغيير الترتيب"""
        if obj.previous_rank and obj.rank:
            return obj.previous_rank - obj.rank  # موجب = تحسن، سالب = تراجع
        return 0

class SectionCompetitionSerializer(serializers.ModelSerializer):
    """مسلسل تنافس الشعب"""
    
    section = SectionBasicSerializer(read_only=True)
    competition_title = serializers.CharField(source='competition.title', read_only=True)
    rank_change = serializers.SerializerMethodField()
    
    class Meta:
        model = SectionCompetition
        fields = [
            'id', 'section', 'competition', 'competition_title',
            'total_points', 'average_score', 'participant_count',
            'rank', 'previous_rank', 'rank_change'
        ]
    
    def get_rank_change(self, obj):
        if obj.previous_rank and obj.rank:
            return obj.previous_rank - obj.rank
        return 0

class CompetitionRoundSerializer(serializers.ModelSerializer):
    """مسلسل جولات المسابقة"""
    
    class Meta:
        model = CompetitionRound
        fields = [
            'id', 'competition', 'round_number', 'title', 'description',
            'start_date', 'end_date', 'points_multiplier'
        ]
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("تاريخ بداية الجولة يجب أن يكون قبل تاريخ النهاية")
        return data

class CompetitionVoteSerializer(serializers.ModelSerializer):
    """مسلسل تصويت المسابقة"""
    
    voter = UserBasicSerializer(read_only=True)
    candidate = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CompetitionVote
        fields = [
            'id', 'competition', 'voter', 'candidate',
            'vote_weight', 'comment', 'created_at'
        ]
        read_only_fields = ['created_at']

class CompetitionRewardSerializer(serializers.ModelSerializer):
    """مسلسل جوائز المسابقة"""
    
    participant = CompetitionParticipantSerializer(read_only=True)
    badge = BadgeSerializer(read_only=True)
    reward_type_display = serializers.CharField(source='get_reward_type_display', read_only=True)
    
    class Meta:
        model = CompetitionReward
        fields = [
            'id', 'competition', 'participant', 'reward_type', 'reward_type_display',
            'title', 'description', 'points_value', 'badge', 'awarded_at'
        ]
        read_only_fields = ['awarded_at']

class CompetitionDetailSerializer(CompetitionSerializer):
    """مسلسل تفاصيل المسابقة"""
    
    participants = CompetitionParticipantSerializer(many=True, read_only=True)
    section_battles = SectionCompetitionSerializer(many=True, read_only=True)
    rounds = CompetitionRoundSerializer(many=True, read_only=True)
    top_participants = serializers.SerializerMethodField()
    my_participation = serializers.SerializerMethodField()
    
    class Meta(CompetitionSerializer.Meta):
        fields = CompetitionSerializer.Meta.fields + [
            'participants', 'section_battles', 'rounds', 
            'top_participants', 'my_participation'
        ]
    
    def get_top_participants(self, obj):
        """أفضل 10 مشاركين"""
        top_participants = obj.participants.order_by('-total_score')[:10]
        return CompetitionParticipantSerializer(top_participants, many=True).data
    
    def get_my_participation(self, obj):
        """مشاركة المستخدم الحالي"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participation = obj.participants.get(user=request.user)
                return CompetitionParticipantSerializer(participation).data
            except CompetitionParticipant.DoesNotExist:
                return None
        return None

class CompetitionStatsSerializer(serializers.Serializer):
    """مسلسل إحصائيات المسابقات"""
    
    total_competitions = serializers.IntegerField()
    active_competitions = serializers.IntegerField()
    finished_competitions = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    average_participants_per_competition = serializers.FloatField()
    most_popular_competition = CompetitionSerializer()
    top_performers = CompetitionParticipantSerializer(many=True)