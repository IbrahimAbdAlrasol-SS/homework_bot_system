from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import (
    Competition, CompetitionParticipant, SectionCompetition,
    CompetitionRound, CompetitionVote, CompetitionReward
)
from .serializers import (
    CompetitionSerializer, CompetitionDetailSerializer,
    CompetitionParticipantSerializer, SectionCompetitionSerializer,
    CompetitionRoundSerializer, CompetitionVoteSerializer,
    CompetitionRewardSerializer, CompetitionStatsSerializer
)
from .utils import CompetitionCalculator, CompetitionRewardManager, CompetitionAnalytics
from core.permissions import IsOwnerOrReadOnly, IsTeacherOrReadOnly

class CompetitionViewSet(viewsets.ModelViewSet):
    """مجموعة عرض المسابقات المتقدمة"""
    
    queryset = Competition.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['competition_type', 'status', 'period', 'is_featured']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'participant_count']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompetitionDetailSerializer
        return CompetitionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # تصفية حسب الشعبة
        section_id = self.request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(sections__id=section_id)
        
        # تصفية حسب المشاركة
        if self.request.query_params.get('my_competitions') == 'true':
            if self.request.user.is_authenticated:
                queryset = queryset.filter(participants__user=self.request.user)
        
        return queryset.annotate(
            participant_count=Count('participants')
        ).distinct()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        """الانضمام للمسابقة"""
        competition = self.get_object()
        user = request.user
        
        # التحقق من حالة المسابقة
        if competition.status != Competition.Status.UPCOMING:
            return Response(
                {'error': 'لا يمكن الانضمام لمسابقة غير قادمة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # التحقق من الحد الأقصى للمشاركين
        if competition.max_participants:
            if competition.participant_count >= competition.max_participants:
                return Response(
                    {'error': 'تم الوصول للحد الأقصى من المشاركين'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # التحقق من المشاركة السابقة
        if CompetitionParticipant.objects.filter(competition=competition, user=user).exists():
            return Response(
                {'error': 'أنت مشارك بالفعل في هذه المسابقة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # إنشاء المشاركة
        participant = CompetitionParticipant.objects.create(
            competition=competition,
            user=user
        )
        
        # تحديث إحصائيات الشعبة إذا كانت المسابقة تشمل الشعب
        if competition.competition_type in [Competition.Type.SECTION, Competition.Type.MIXED]:
            if hasattr(user, 'section') and user.section:
                section_competition, created = SectionCompetition.objects.get_or_create(
                    competition=competition,
                    section=user.section,
                    defaults={'participant_count': 0}
                )
                section_competition.participant_count = F('participant_count') + 1
                section_competition.save()
        
        serializer = CompetitionParticipantSerializer(participant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        """مغادرة المسابقة"""
        competition = self.get_object()
        user = request.user
        
        try:
            participant = CompetitionParticipant.objects.get(
                competition=competition, user=user
            )
            
            # التحقق من إمكانية المغادرة
            if competition.status == Competition.Status.ACTIVE:
                return Response(
                    {'error': 'لا يمكن مغادرة مسابقة نشطة'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            participant.delete()
            
            # تحديث إحصائيات الشعبة
            if competition.competition_type in [Competition.Type.SECTION, Competition.Type.MIXED]:
                if hasattr(user, 'section') and user.section:
                    try:
                        section_competition = SectionCompetition.objects.get(
                            competition=competition, section=user.section
                        )
                        section_competition.participant_count = F('participant_count') - 1
                        section_competition.save()
                    except SectionCompetition.DoesNotExist:
                        pass
            
            return Response({'message': 'تم ترك المسابقة بنجاح'})
            
        except CompetitionParticipant.DoesNotExist:
            return Response(
                {'error': 'أنت لست مشارك في هذه المسابقة'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """المسابقات النشطة"""
        now = timezone.now()
        active_competitions = self.get_queryset().filter(
            start_date__lte=now,
            end_date__gte=now,
            status=Competition.Status.ACTIVE
        )
        
        serializer = self.get_serializer(active_competitions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """المسابقات المميزة"""
        featured_competitions = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(featured_competitions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_competitions(self, request):
        """مسابقاتي"""
        user_competitions = self.get_queryset().filter(
            participants__user=request.user
        )
        serializer = self.get_serializer(user_competitions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def leaderboard(self, request, pk=None):
        """لوحة المتصدرين"""
        competition = self.get_object()
        participants = competition.participants.order_by('-total_score', 'joined_at')
        
        # تطبيق التصفية
        section_id = request.query_params.get('section')
        if section_id:
            participants = participants.filter(user__section__id=section_id)
        
        # التصفح
        page = self.paginate_queryset(participants)
        if page is not None:
            serializer = CompetitionParticipantSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CompetitionParticipantSerializer(participants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def section_battles(self, request, pk=None):
        """معارك الشعب"""
        competition = self.get_object()
        
        if competition.competition_type not in [Competition.Type.SECTION, Competition.Type.MIXED]:
            return Response(
                {'error': 'هذه المسابقة لا تدعم معارك الشعب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        section_battles = competition.section_battles.order_by('-total_points')
        serializer = SectionCompetitionSerializer(section_battles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacherOrReadOnly])
    def update_rankings(self, request, pk=None):
        """تحديث الترتيب"""
        competition = self.get_object()
        
        # تحديث نقاط المشاركين
        CompetitionCalculator.update_participant_scores(competition)
        
        # تحديث ترتيب المشاركين
        CompetitionCalculator.update_participant_rankings(competition)
        
        # تحديث ترتيب الشعب
        if competition.competition_type in [Competition.Type.SECTION, Competition.Type.MIXED]:
            CompetitionCalculator.update_section_rankings(competition)
        
        return Response({'message': 'تم تحديث الترتيب بنجاح'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsTeacherOrReadOnly])
    def award_prizes(self, request, pk=None):
        """منح الجوائز"""
        competition = self.get_object()
        
        if competition.status != Competition.Status.FINISHED:
            return Response(
                {'error': 'يمكن منح الجوائز فقط للمسابقات المنتهية'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # منح الجوائز
        rewards = CompetitionRewardManager.award_competition_prizes(competition)
        
        serializer = CompetitionRewardSerializer(rewards, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """إحصائيات المسابقات"""
        stats = CompetitionAnalytics.get_general_stats()
        serializer = CompetitionStatsSerializer(stats)
        return Response(serializer.data)

class CompetitionParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """مجموعة عرض مشاركين المسابقة"""
    
    queryset = CompetitionParticipant.objects.all()
    serializer_class = CompetitionParticipantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['competition', 'user']
    ordering_fields = ['total_score', 'rank', 'joined_at']
    ordering = ['-total_score']

class CompetitionVoteViewSet(viewsets.ModelViewSet):
    """مجموعة عرض تصويتات المسابقة"""
    
    queryset = CompetitionVote.objects.all()
    serializer_class = CompetitionVoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().filter(voter=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(voter=self.request.user)

class CompetitionRewardViewSet(viewsets.ReadOnlyModelViewSet):
    """مجموعة عرض جوائز المسابقة"""
    
    queryset = CompetitionReward.objects.all()
    serializer_class = CompetitionRewardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['competition', 'participant', 'reward_type']