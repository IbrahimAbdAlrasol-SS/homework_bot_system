from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Badge, UserBadge, Competition, CompetitionParticipant
from .serializers import (
    BadgeSerializer, UserBadgeSerializer, CompetitionSerializer,
    CompetitionDetailSerializer, CompetitionParticipantSerializer,
    BadgeStatisticsSerializer
)
from core.permissions import IsAdminOrReadOnly, IsSuperAdminOnly
from core.pagination import StandardResultsSetPagination


class BadgeViewSet(viewsets.ModelViewSet):
    """مجموعة عرض الشارات"""
    
    queryset = Badge.objects.filter(is_active=True)
    serializer_class = BadgeSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['badge_type', 'rarity', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'rarity', 'created_at']
    ordering = ['rarity', 'name']
    pagination_class = StandardResultsSetPagination
    
    @action(detail=False, methods=['get'])
    def my_badges(self, request):
        """شارات المستخدم الحالي"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'يجب تسجيل الدخول أولاً'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_badges = UserBadge.objects.filter(
            user=request.user
        ).select_related('badge')
        
        serializer = UserBadgeSerializer(user_badges, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """الشارات المتاحة للحصول عليها"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'يجب تسجيل الدخول أولاً'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # الشارات التي لم يحصل عليها المستخدم
        earned_badge_ids = UserBadge.objects.filter(
            user=request.user
        ).values_list('badge_id', flat=True)
        
        available_badges = self.get_queryset().exclude(
            id__in=earned_badge_ids
        )
        
        page = self.paginate_queryset(available_badges)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(available_badges, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """إحصائيات الشارات"""
        total_badges = Badge.objects.filter(is_active=True).count()
        
        if request.user.is_authenticated:
            earned_badges = UserBadge.objects.filter(user=request.user).count()
            
            # إحصائيات حسب الندرة
            user_badges = UserBadge.objects.filter(
                user=request.user
            ).select_related('badge')
            
            stats = {
                'total_badges': total_badges,
                'earned_badges': earned_badges,
                'common_badges': user_badges.filter(badge__rarity='common').count(),
                'rare_badges': user_badges.filter(badge__rarity='rare').count(),
                'epic_badges': user_badges.filter(badge__rarity='epic').count(),
                'legendary_badges': user_badges.filter(badge__rarity='legendary').count(),
                'completion_rate': round((earned_badges / total_badges) * 100, 2) if total_badges > 0 else 0
            }
        else:
            stats = {
                'total_badges': total_badges,
                'earned_badges': 0,
                'common_badges': 0,
                'rare_badges': 0,
                'epic_badges': 0,
                'legendary_badges': 0,
                'completion_rate': 0
            }
        
        serializer = BadgeStatisticsSerializer(stats)
        return Response(serializer.data)


class CompetitionViewSet(viewsets.ModelViewSet):
    """مجموعة عرض المسابقات"""
    
    queryset = Competition.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['competition_type', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompetitionDetailSerializer
        return CompetitionSerializer
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """الانضمام للمسابقة"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'يجب تسجيل الدخول أولاً'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        competition = self.get_object()
        
        # التحقق من حالة المسابقة
        if competition.status != 'active':
            return Response(
                {'error': 'المسابقة غير نشطة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التحقق من عدد المشاركين
        if (competition.max_participants and 
            competition.participants.count() >= competition.max_participants):
            return Response(
                {'error': 'وصل عدد المشاركين للحد الأقصى'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التحقق من المشاركة السابقة
        if CompetitionParticipant.objects.filter(
            competition=competition, user=request.user
        ).exists():
            return Response(
                {'error': 'أنت مشارك بالفعل في هذه المسابقة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # إنشاء المشاركة
        participant = CompetitionParticipant.objects.create(
            competition=competition,
            user=request.user
        )
        
        serializer = CompetitionParticipantSerializer(participant)
        return Response({
            'message': 'تم الانضمام للمسابقة بنجاح',
            'participant': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """المسابقات النشطة"""
        now = timezone.now()
        active_competitions = self.get_queryset().filter(
            start_date__lte=now,
            end_date__gte=now,
            status='active'
        )
        
        page = self.paginate_queryset(active_competitions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(active_competitions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_competitions(self, request):
        """مسابقات المستخدم"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'يجب تسجيل الدخول أولاً'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        my_competitions = self.get_queryset().filter(
            participants__user=request.user
        ).distinct()
        
        page = self.paginate_queryset(my_competitions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(my_competitions, many=True)
        return Response(serializer.data)