from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompetitionViewSet, CompetitionParticipantViewSet,
    CompetitionVoteViewSet, CompetitionRewardViewSet
)

router = DefaultRouter()
router.register(r'competitions', CompetitionViewSet)
router.register(r'participants', CompetitionParticipantViewSet)
router.register(r'votes', CompetitionVoteViewSet)
router.register(r'rewards', CompetitionRewardViewSet)

urlpatterns = [
    path('', include(router.urls)),
]