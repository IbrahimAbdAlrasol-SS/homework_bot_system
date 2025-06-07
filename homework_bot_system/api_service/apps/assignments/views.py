from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
from django.utils import timezone
from .models import Assignment
from .serializers import (
    AssignmentSerializer, AssignmentDetailSerializer, CreateAssignmentSerializer
)
from core.permissions import IsAdminOrReadOnly, IsSectionAdminOrOwner
from apps.users.models import User

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAssignmentSerializer
        elif self.action == 'retrieve':
            return AssignmentDetailSerializer
        return AssignmentSerializer
    
    def get_queryset(self):
        queryset = Assignment.objects.select_related('section', 'created_by')
        
        # Filter by section if user is section admin
        if self.request.user.role == User.Role.SECTION_ADMIN:
            queryset = queryset.filter(section__admin=self.request.user)
        elif self.request.user.role == User.Role.STUDENT:
            queryset = queryset.filter(section=self.request.user.section)
        
        # Filter by section
        section_id = self.request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.annotate(
            submissions_count=Count('submissions'),
            pending_submissions=Count(
                'submissions', 
                filter=Q(submissions__status='pending')
            )
        )
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """الحصول على تسليمات الواجب"""
        assignment = self.get_object()
        submissions = assignment.submissions.select_related('user')
        
        # فلترة حسب الحالة
        status_filter = request.query_params.get('status')
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        
        from apps.submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """إحصائيات الواجب"""
        assignment = self.get_object()
        
        total_students = assignment.section.students.filter(
            role=User.Role.STUDENT
        ).count()
        
        submissions = assignment.submissions.all()
        total_submissions = submissions.count()
        approved_submissions = submissions.filter(status='approved').count()
        pending_submissions = submissions.filter(status='pending').count()
        rejected_submissions = submissions.filter(status='rejected').count()
        
        stats = {
            'total_students': total_students,
            'total_submissions': total_submissions,
            'approved_submissions': approved_submissions,
            'pending_submissions': pending_submissions,
            'rejected_submissions': rejected_submissions,
            'submission_rate': (total_submissions / total_students * 100) if total_students > 0 else 0,
            'approval_rate': (approved_submissions / total_submissions * 100) if total_submissions > 0 else 0,
            'is_overdue': assignment.due_date < timezone.now(),
            'days_remaining': (assignment.due_date - timezone.now()).days if assignment.due_date > timezone.now() else 0
        }
        
        return Response(stats)

class UpcomingAssignmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        now = timezone.now()
        
        if request.user.role == User.Role.STUDENT:
            assignments = Assignment.objects.filter(
                section=request.user.section,
                due_date__gt=now,
                is_active=True
            )
        elif request.user.role == User.Role.SECTION_ADMIN:
            assignments = Assignment.objects.filter(
                section__admin=request.user,
                due_date__gt=now,
                is_active=True
            )
        else:
            assignments = Assignment.objects.filter(
                due_date__gt=now,
                is_active=True
            )
        
        assignments = assignments.order_by('due_date')[:10]
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

class OverdueAssignmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        now = timezone.now()
        
        if request.user.role == User.Role.STUDENT:
            assignments = Assignment.objects.filter(
                section=request.user.section,
                due_date__lt=now,
                is_active=True
            )
        elif request.user.role == User.Role.SECTION_ADMIN:
            assignments = Assignment.objects.filter(
                section__admin=request.user,
                due_date__lt=now,
                is_active=True
            )
        else:
            assignments = Assignment.objects.filter(
                due_date__lt=now,
                is_active=True
            )
        
        assignments = assignments.order_by('-due_date')[:10]
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

class AssignmentSubmissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, assignment_id):
        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Response(
                {'error': 'الواجب غير موجود'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # التحقق من الصلاحيات
        if (request.user.role == User.Role.SECTION_ADMIN and 
            assignment.section.admin != request.user):
            return Response(
                {'error': 'ليس لديك صلاحية للوصول لهذا الواجب'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        submissions = assignment.submissions.select_related('user')
        
        # فلترة حسب الحالة
        status_filter = request.query_params.get('status')
        if status_filter:
            submissions = submissions.filter(status=status_filter)
        
        from apps.submissions.serializers import SubmissionSerializer
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

class AssignmentStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, assignment_id):
        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Response(
                {'error': 'الواجب غير موجود'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        total_students = assignment.section.students.filter(
            role=User.Role.STUDENT
        ).count()
        
        submissions = assignment.submissions.all()
        total_submissions = submissions.count()
        approved_submissions = submissions.filter(status='approved').count()
        pending_submissions = submissions.filter(status='pending').count()
        rejected_submissions = submissions.filter(status='rejected').count()
        
        stats = {
            'total_students': total_students,
            'total_submissions': total_submissions,
            'approved_submissions': approved_submissions,
            'pending_submissions': pending_submissions,
            'rejected_submissions': rejected_submissions,
            'submission_rate': (total_submissions / total_students * 100) if total_students > 0 else 0,
            'approval_rate': (approved_submissions / total_submissions * 100) if total_submissions > 0 else 0,
            'is_overdue': assignment.due_date < timezone.now(),
            'days_remaining': (assignment.due_date - timezone.now()).days if assignment.due_date > timezone.now() else 0
        }
        
        return Response(stats)