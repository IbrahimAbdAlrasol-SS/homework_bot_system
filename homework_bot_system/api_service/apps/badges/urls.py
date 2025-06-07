from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.BadgeViewSet, basename='badge')

urlpatterns = [
    path('', include(router.urls)),
    path('my-badges/', views.MyBadgesView.as_view(), name='my-badges'),
    path('leaderboard/', views.BadgeLeaderboardView.as_view(), name='badge-leaderboard'),
]