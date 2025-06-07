from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Submission, SubmissionFile
from .serializers import (
    SubmissionSerializer, SubmissionDetailSerializer,
    SubmissionCreateSerializer, SubmissionReviewSerializer,
    SubmissionStatisticsSerializer, SubmissionFileSerializer
)
from core.permissions import IsOwnerOrAdmin, IsSectionAdminOrOwner
from core.pagination import StandardResultsSetPagination


class SubmissionViewSet(viewsets.ModelViewSet):
    """مجموعة عرض التسليمات"""
    
    queryset = Submission.objects.select_related(
        'student', 'assignment', 'reviewed_by'
    ).prefetch_related('files')
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'grade', 'is_late', 'is_excellent', 'assignment']
    search_fields = ['student__full_name', 'assignment__title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'points_earned']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionCreateSerializer
        elif self.action == 'review':
            return SubmissionReviewSerializer
        elif self.action == 'retrieve':
            return SubmissionDetailSerializer
        return SubmissionSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['review', 'destroy']:
            permission_classes = [IsSectionAdminOrOwner]
        else:
            permission_classes = [IsOwnerOrAdmin]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        
        if user.role == 'student':
            # الطلاب يرون تسليماتهم فقط
            queryset = queryset.filter(student=user)
        elif user.role == 'section_admin':
            # أدمن الشعبة يرى تسليمات شعبته فقط
            queryset = queryset.filter(student__section=user.section)
        # المسؤول العام يرى كل التسليمات
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsSectionAdminOrOwner])
    def review(self, request, pk=None):
        """مراجعة التسليم"""
        submission = self.get_object()
        serializer = self.get_serializer(submission, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'تم مراجعة التسليم بنجاح',
                'submission': SubmissionDetailSerializer(submission).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_submissions(self, request):
        """تسليمات المستخدم الحالي"""
        if request.user.role != 'student':
            return Response(
                {'error': 'هذه الخدمة متاحة للطلاب فقط'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submissions = self.get_queryset().filter(student=request.user)
        page = self.paginate_queryset(submissions)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """التسليمات في انتظار المراجعة"""
        if request.user.role not in ['section_admin', 'super_admin']:
            return Response(
                {'error': 'غير مصرح لك بالوصول'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submissions = self.get_queryset().filter(status='pending')
        page = self.paginate_queryset(submissions)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """إحصائيات التسليمات"""
        queryset = self.get_queryset()
        
        stats = {
            'total_submissions': queryset.count(),
            'approved_submissions': queryset.filter(status='approved').count(),
            'rejected_submissions': queryset.filter(status='rejected').count(),
            'pending_submissions': queryset.filter(status='pending').count(),
            'late_submissions': queryset.filter(is_late=True).count(),
            'excellent_submissions': queryset.filter(is_excellent=True).count(),
        }
        
        # حساب معدل القبول
        total = stats['total_submissions']
        if total > 0:
            stats['approval_rate'] = round(
                (stats['approved_submissions'] / total) * 100, 2
            )
            stats['average_points'] = queryset.filter(
                status='approved'
            ).aggregate(avg=Avg('points_earned'))['avg'] or 0
        else:
            stats['approval_rate'] = 0
            stats['average_points'] = 0
        
        serializer = SubmissionStatisticsSerializer(stats)
        return Response(serializer.data)