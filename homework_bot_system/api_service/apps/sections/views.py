from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, Avg
from django.contrib.auth import get_user_model
from .models import Section
from .serializers import (
    SectionSerializer, SectionDetailSerializer, SectionStatisticsSerializer
)
from apps.users.serializers import UserSerializer
from apps.assignments.serializers import AssignmentSerializer
from core.permissions import IsAdminOrReadOnly, IsSuperAdminOnly

User = get_user_model()

class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SectionDetailSerializer
        return SectionSerializer
    
    def get_queryset(self):
        queryset = Section.objects.select_related('admin')
        
        # Filter by section if user is section admin
        if self.request.user.role == User.Role.SECTION_ADMIN:
            queryset = queryset.filter(admin=self.request.user)
        
        # Filter by study type
        study_type = self.request.query_params.get('study_type')
        if study_type:
            queryset = queryset.filter(study_type=study_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """الحصول على طلاب الشعبة"""
        section = self.get_object()
        students = section.students.filter(role=User.Role.STUDENT)
        
        # ترتيب حسب النقاط
        students = students.order_by('-points', '-excellence_points')
        
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """الحصول على واجبات الشعبة"""
        section = self.get_object()
        assignments = section.assignments.filter(is_active=True)
        
        # ترتيب حسب تاريخ الاستحقاق
        assignments = assignments.order_by('due_date')
        
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def ranking(self, request, pk=None):
        """ترتيب طلاب الشعبة"""
        section = self.get_object()
        students = section.students.filter(
            role=User.Role.STUDENT
        ).order_by('-points', '-excellence_points')
        
        # إضافة رقم الترتيب
        for i, student in enumerate(students, 1):
            student.rank = i
        
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """إحصائيات الشعبة"""
        section = self.get_object()
        
        stats = section.calculate_section_stats()
        serializer = SectionStatisticsSerializer(stats)
        return Response(serializer.data)

class SectionStudentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, section_id):
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {'error': 'الشعبة غير موجودة'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # التحقق من الصلاحيات
        if (request.user.role == User.Role.SECTION_ADMIN and 
            section.admin != request.user):
            return Response(
                {'error': 'ليس لديك صلاحية للوصول لهذه الشعبة'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        students = section.students.filter(role=User.Role.STUDENT)
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)

class SectionAssignmentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, section_id):
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {'error': 'الشعبة غير موجودة'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        assignments = section.assignments.filter(is_active=True)
        
        # فلترة حسب الحالة
        status_filter = request.query_params.get('status')
        if status_filter:
            assignments = assignments.filter(status=status_filter)
        
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

class SectionRankingView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, section_id):
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {'error': 'الشعبة غير موجودة'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        students = section.students.filter(
            role=User.Role.STUDENT
        ).order_by('-points', '-excellence_points')
        
        # إضافة رقم الترتيب
        for i, student in enumerate(students, 1):
            student.rank = i
        
        from apps.users.serializers import UserRankingSerializer
        serializer = UserRankingSerializer(students, many=True)
        return Response(serializer.data)

class SectionStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, section_id):
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            return Response(
                {'error': 'الشعبة غير موجودة'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        stats = section.calculate_section_stats()
        serializer = SectionStatisticsSerializer(stats)
        return Response(serializer.data)