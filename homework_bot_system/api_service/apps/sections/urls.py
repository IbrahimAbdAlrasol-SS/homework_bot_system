from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.SectionViewSet, basename='section')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:section_id>/students/', views.SectionStudentsView.as_view(), name='section-students'),
    path('<int:section_id>/assignments/', views.SectionAssignmentsView.as_view(), name='section-assignments'),
    path('<int:section_id>/ranking/', views.SectionRankingView.as_view(), name='section-ranking'),
    path('<int:section_id>/statistics/', views.SectionStatisticsView.as_view(), name='section-statistics'),
]