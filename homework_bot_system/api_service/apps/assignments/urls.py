from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.AssignmentViewSet, basename='assignment')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:assignment_id>/submissions/', views.AssignmentSubmissionsView.as_view(), name='assignment-submissions'),
    path('<int:assignment_id>/statistics/', views.AssignmentStatisticsView.as_view(), name='assignment-statistics'),
    path('upcoming/', views.UpcomingAssignmentsView.as_view(), name='upcoming-assignments'),
    path('overdue/', views.OverdueAssignmentsView.as_view(), name='overdue-assignments'),
]