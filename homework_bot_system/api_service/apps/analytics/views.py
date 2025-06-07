from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import PointsHistory, DailyStatistics, ActivityLog
from .serializers import (
    PointsHistorySerializer, DailyStatisticsSerializer,
    ActivityLogSerializer, UserAnalyticsSerializer,
    SectionAnalyticsSerializer, GlobalAnalyticsSerializer
)
from apps.users.models import User
from apps.sections.models import Section
from apps.assignments.models import Assignment
from apps.submissions.models import Submission
from apps.badges.models import Badge, UserBadge, Competition
from core.permissions import IsOwnerOrAdmin, IsSectionAdminOrOwner, IsSuperAdminOnly
from core.pagination import StandardResultsSetPagination


class PointsHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """مجموعة عرض تاريخ النقاط"""
    
    queryset = PointsHistory.objects.select_related('user', 'assignment')
    serializer_class = PointsHistorySerializer
    permission_classes = [IsOwnerOrAdmin]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user', 'assignment']
    ordering_fields = ['created_at', 'points_change']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'student':
            # الطلاب يرون تاريخ نقاطهم فقط
            queryset = queryset.filter(user=user)
        elif user.role == 'section_admin':
            # أدمن الشعبة يرى تاريخ نقاط طلاب شعبته
            queryset = queryset.filter(user__section=user.section)
        # المسؤول العام يرى كل التاريخ
        
        return queryset


class DailyStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """مجموعة عرض الإحصائيات اليومية"""
    
    queryset = DailyStatistics.objects.select_related('section')
    serializer_class = DailyStatisticsSerializer
    permission_classes = [IsSectionAdminOrOwner]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['section', 'date']
    ordering_fields = ['date']
    ordering = ['-date']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'section_admin':
            # أدمن الشعبة يرى إحصائيات شعبته فقط
            queryset = queryset.filter(section=user.section)
        # المسؤول العام يرى كل الإحصائيات
        
        return queryset


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """مجموعة عرض سجل الأنشطة"""
    
    queryset = ActivityLog.objects.select_related('user')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsOwnerOrAdmin]
    
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user', 'action']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'student':
            # الطلاب يرون أنشطتهم فقط
            queryset = queryset.filter(user=user)
        elif user.role == 'section_admin':
            # أدمن الشعبة يرى أنشطة طلاب شعبته
            queryset = queryset.filter(user__section=user.section)
        # المسؤول العام يرى كل الأنشطة
        
        return queryset


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_analytics(request):
    """تحليلات المستخدم"""
    user = request.user
    
    # النقاط
    total_points = user.points
    
    # نقاط هذا الشهر
    start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    points_this_month = PointsHistory.objects.filter(
        user=user,
        created_at__gte=start_of_month,
        points_change__gt=0
    ).aggregate(total=Sum('points_change'))['total'] or 0
    
    # التسليمات
    submissions = Submission.objects.filter(student=user)
    total_submissions = submissions.count()
    approved_submissions = submissions.filter(status='approved').count()
    rejected_submissions = submissions.filter(status='rejected').count()
    late_submissions = submissions.filter(is_late=True).count()
    
    # الشارات
    badges_count = UserBadge.objects.filter(user=user).count()
    
    # الترتيب
    if user.section:
        section_users = User.objects.filter(
            section=user.section, role='student'
        ).order_by('-points')
        rank_in_section = list(section_users.values_list('id', flat=True)).index(user.id) + 1
    else:
        rank_in_section = 0
    
    all_users = User.objects.filter(role='student').order_by('-points')
    rank_global = list(all_users.values_list('id', flat=True)).index(user.id) + 1
    
    # معدلات
    approval_rate = (approved_submissions / total_submissions * 100) if total_submissions > 0 else 0
    avg_points = submissions.filter(status='approved').aggregate(
        avg=Avg('points_earned')
    )['avg'] or 0
    
    # اليوم الأكثر نشاطاً
    activity_by_day = ActivityLog.objects.filter(
        user=user
    ).extra(
        select={'day': 'DAYOFWEEK(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('-count').first()
    
    days = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
    most_active_day = days[activity_by_day['day'] - 1] if activity_by_day else 'غير محدد'
    
    # اتجاه النقاط (آخر 7 أيام)
    points_trend = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        points_change = PointsHistory.objects.filter(
            user=user,
            created_at__date=date
        ).aggregate(total=Sum('points_change'))['total'] or 0
        
        points_trend.append({
            'date': date.strftime('%Y-%m-%d'),
            'points': points_change
        })
    
    points_trend.reverse()
    
    analytics_data = {
        'total_points': total_points,
        'points_this_month': points_this_month,
        'total_submissions': total_submissions,
        'approved_submissions': approved_submissions,
        'rejected_submissions': rejected_submissions,
        'late_submissions': late_submissions,
        'submission_streak': user.submission_streak,
        'badges_count': badges_count,
        'rank_in_section': rank_in_section,
        'rank_global': rank_global,
        'approval_rate': round(approval_rate, 2),
        'average_points_per_submission': round(avg_points, 2),
        'most_active_day': most_active_day,
        'points_trend': points_trend
    }
    
    serializer = UserAnalyticsSerializer(analytics_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsSectionAdminOrOwner])
def section_analytics(request, section_id=None):
    """تحليلات الشعبة"""
    user = request.user
    
    # تحديد الشعبة
    if section_id:
        try:
            section = Section.objects.get(id=section_id)
            # التحقق من الصلاحية
            if user.role == 'section_admin' and user.section != section:
                return Response(
                    {'error': 'غير مصرح لك بالوصول لهذه الشعبة'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Section.DoesNotExist:
            return Response(
                {'error': 'الشعبة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        section = user.section
    
    if not section:
        return Response(
            {'error': 'لا توجد شعبة محددة'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # الطلاب
    students = User.objects.filter(section=section, role='student')
    total_students = students.count()
    
    # الطلاب النشطين (لديهم نشاط في آخر 7 أيام)
    week_ago = timezone.now() - timedelta(days=7)
    active_students = students.filter(
        last_activity__gte=week_ago
    ).count()
    
    # الواجبات والتسليمات
    assignments = Assignment.objects.filter(section=section)
    total_assignments = assignments.count()
    
    submissions = Submission.objects.filter(student__section=section)
    total_submissions = submissions.count()
    pending_submissions = submissions.filter(status='pending').count()
    approved_submissions = submissions.filter(status='approved').count()
    rejected_submissions = submissions.filter(status='rejected').count()
    late_submissions = submissions.filter(is_late=True).count()
    
    # المعدلات
    average_points = students.aggregate(avg=Avg('points'))['avg'] or 0
    submission_rate = (total_submissions / (total_assignments * total_students) * 100) if (total_assignments * total_students) > 0 else 0
    approval_rate = (approved_submissions / total_submissions * 100) if total_submissions > 0 else 0
    
    # أفضل الطلاب
    top_students = students.order_by('-points')[:5].values(
        'id', 'full_name', 'points', 'submission_streak'
    )
    
    # الإحصائيات اليومية (آخر 7 أيام)
    daily_stats = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        day_submissions = submissions.filter(created_at__date=date).count()
        day_approved = submissions.filter(
            created_at__date=date, status='approved'
        ).count()
        
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'submissions': day_submissions,
            'approved': day_approved
        })
    
    daily_stats.reverse()
    
    analytics_data = {
        'total_students': total_students,
        'active_students': active_students,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'pending_submissions': pending_submissions,
        'approved_submissions': approved_submissions,
        'rejected_submissions': rejected_submissions,
        'late_submissions': late_submissions,
        'average_points': round(average_points, 2),
        'submission_rate': round(submission_rate, 2),
        'approval_rate': round(approval_rate, 2),
        'top_students': list(top_students),
        'daily_stats': daily_stats
    }
    
    serializer = SectionAnalyticsSerializer(analytics_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsSuperAdminOnly])
def global_analytics(request):
    """التحليلات العامة"""
    
    # المستخدمون
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    
    # الشعب والواجبات
    total_sections = Section.objects.count()
    total_assignments = Assignment.objects.count()
    total_submissions = Submission.objects.count()
    
    # الشارات والمسابقات
    total_badges = Badge.objects.filter(is_active=True).count()
    total_competitions = Competition.objects.count()
    active_competitions = Competition.objects.filter(
        status='active',
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).count()
    
    # المعدلات
    average_points = User.objects.filter(
        role='student'
    ).aggregate(avg=Avg('points'))['avg'] or 0
    
    submission_rate = (total_submissions / (total_assignments * total_students) * 100) if (total_assignments * total_students) > 0 else 0
    
    approved_submissions = Submission.objects.filter(status='approved').count()
    approval_rate = (approved_submissions / total_submissions * 100) if total_submissions > 0 else 0
    
    # أفضل الشعب
    top_sections = Section.objects.annotate(
        avg_points=Avg('students__points'),
        total_submissions=Count('students__submissions')
    ).order_by('-avg_points')[:5].values(
        'id', 'name', 'avg_points', 'total_submissions'
    )
    
    # الأنشطة الحديثة
    recent_activities = ActivityLog.objects.select_related(
        'user'
    ).order_by('-created_at')[:10].values(
        'user__full_name', 'action', 'description', 'created_at'
    )
    
    analytics_data = {
        'total_users': total_users,
        'total_students': total_students,
        'total_sections': total_sections,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'total_badges': total_badges,
        'total_competitions': total_competitions,
        'active_competitions': active_competitions,
        'average_points_per_user': round(average_points, 2),
        'submission_rate': round(submission_rate, 2),
        'approval_rate': round(approval_rate, 2),
        'top_sections': list(top_sections),
        'recent_activities': list(recent_activities)
    }
    
    serializer = GlobalAnalyticsSerializer(analytics_data)
    return Response(serializer.data)