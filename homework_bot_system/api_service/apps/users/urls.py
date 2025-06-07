from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('ranking/', views.UserRankingView.as_view(), name='user-ranking'),
    path('statistics/', views.UserStatisticsView.as_view(), name='user-statistics'),
    path('change-personality/', views.ChangePersonalityView.as_view(), name='change-personality'),
]