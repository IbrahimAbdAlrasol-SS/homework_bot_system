from rest_framework import serializers
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from .models import PointsHistory, DailyStatistics, ActivityLog
from apps.users.serializers import UserProfileSerializer
from apps.sections.serializers import SectionSerializer


class PointsHistorySerializer(serializers.ModelSerializer):
    """مسلسل تاريخ النقاط"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = PointsHistory
        fields = [
            'id', 'user', 'user_name', 'points_change', 'reason',
            'total_points_after', 'assignment', 'assignment_title',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'total_points_after', 'created_at']


class DailyStatisticsSerializer(serializers.ModelSerializer):
    """مسلسل الإحصائيات اليومية"""
    
    section_name = serializers.CharField(source='section.name', read_only=True)
    submission_rate = serializers.SerializerMethodField()
    approval_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyStatistics
        fields = [
            'id', 'date', 'section', 'section_name', 'total_assignments',
            'total_submissions', 'approved_submissions', 'rejected_submissions',
            'late_submissions', 'active_students', 'average_points',
            'submission_rate', 'approval_rate'
        ]
        read_only_fields = ['id']
    
    def get_submission_rate(self, obj):
        """معدل التسليم"""
        if obj.total_assignments > 0:
            return round((obj.total_submissions / obj.total_assignments) * 100, 2)
        return 0
    
    def get_approval_rate(self, obj):
        """معدل القبول"""
        if obj.total_submissions > 0:
            return round((obj.approved_submissions / obj.total_submissions) * 100, 2)
        return 0


class ActivityLogSerializer(serializers.ModelSerializer):
    """مسلسل سجل الأنشطة"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_name', 'action', 'action_display',
            'description', 'ip_address', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class UserAnalyticsSerializer(serializers.Serializer):
    """مسلسل تحليلات المستخدم"""
    
    total_points = serializers.IntegerField()
    points_this_month = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    approved_submissions = serializers.IntegerField()
    rejected_submissions = serializers.IntegerField()
    late_submissions = serializers.IntegerField()
    submission_streak = serializers.IntegerField()
    badges_count = serializers.IntegerField()
    rank_in_section = serializers.IntegerField()
    rank_global = serializers.IntegerField()
    approval_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_points_per_submission = serializers.DecimalField(max_digits=10, decimal_places=2)
    most_active_day = serializers.CharField()
    points_trend = serializers.ListField(child=serializers.DictField())


class SectionAnalyticsSerializer(serializers.Serializer):
    """مسلسل تحليلات الشعبة"""
    
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    approved_submissions = serializers.IntegerField()
    rejected_submissions = serializers.IntegerField()
    late_submissions = serializers.IntegerField()
    average_points = serializers.DecimalField(max_digits=10, decimal_places=2)
    submission_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    approval_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    top_students = serializers.ListField(child=serializers.DictField())
    daily_stats = serializers.ListField(child=serializers.DictField())


class GlobalAnalyticsSerializer(serializers.Serializer):
    """مسلسل التحليلات العامة"""
    
    total_users = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_sections = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    total_badges = serializers.IntegerField()
    total_competitions = serializers.IntegerField()
    active_competitions = serializers.IntegerField()
    average_points_per_user = serializers.DecimalField(max_digits=10, decimal_places=2)
    submission_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    approval_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    top_sections = serializers.ListField(child=serializers.DictField())
    recent_activities = serializers.ListField(child=serializers.DictField())