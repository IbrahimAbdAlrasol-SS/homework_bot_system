from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from .models import User
from .serializers import (
    UserSerializer, UserProfileSerializer, ChangePersonalitySerializer,
    UserRankingSerializer
)
from core.permissions import IsAdminOrReadOnly

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        queryset = User.objects.select_related('section')
        
        # Filter by section if user is section admin
        if self.request.user.role == User.Role.SECTION_ADMIN:
            queryset = queryset.filter(section=self.request.user.section)
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        # Filter by section
        section_id = self.request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
            
        return queryset

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # Add statistics
        user.total_submissions = user.submissions.count()
        user.approved_submissions = user.submissions.filter(
            status='approved'
        ).count()
        
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserRankingView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get ranking scope
        scope = request.query_params.get('scope', 'section')  # section, global
        
        if scope == 'global':
            users = User.objects.filter(role=User.Role.STUDENT)
        else:
            users = User.objects.filter(
                role=User.Role.STUDENT,
                section=request.user.section
            )
        
        # Order by points and add rank
        users = users.order_by('-points', '-excellence_points')
        
        # Add rank number
        for i, user in enumerate(users, 1):
            user.rank = i
        
        serializer = UserRankingSerializer(users, many=True)
        return Response(serializer.data)

class UserStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        stats = {
            'total_points': user.points,
            'excellence_points': user.excellence_points,
            'submission_streak': user.submission_streak,
            'penalty_counter': user.penalty_counter,
            'rank_title': user.rank_title,
            'total_submissions': user.submissions.count(),
            'approved_submissions': user.submissions.filter(
                status='approved'
            ).count(),
            'pending_submissions': user.submissions.filter(
                status='pending'
            ).count(),
            'rejected_submissions': user.submissions.filter(
                status='rejected'
            ).count(),
            'badges_count': user.user_badges.count(),
            'section_rank': self._get_section_rank(user),
            'global_rank': self._get_global_rank(user),
        }
        
        return Response(stats)
    
    def _get_section_rank(self, user):
        if not user.section:
            return None
        
        better_users = User.objects.filter(
            section=user.section,
            role=User.Role.STUDENT,
            points__gt=user.points
        ).count()
        
        return better_users + 1
    
    def _get_global_rank(self, user):
        better_users = User.objects.filter(
            role=User.Role.STUDENT,
            points__gt=user.points
        ).count()
        
        return better_users + 1

class ChangePersonalityView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePersonalitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            return Response({
                'message': 'تم تغيير شخصية البوت بنجاح',
                'personality': serializer.validated_data['personality']
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)