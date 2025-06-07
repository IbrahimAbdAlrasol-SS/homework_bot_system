from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    path('section-performance/', views.SectionPerformanceView.as_view(), name='section-performance'),
    path('student-progress/', views.StudentProgressView.as_view(), name='student-progress'),
    path('competition-stats/', views.CompetitionStatsView.as_view(), name='competition-stats'),
    path('daily-stats/', views.DailyStatsView.as_view(), name='daily-stats'),
]