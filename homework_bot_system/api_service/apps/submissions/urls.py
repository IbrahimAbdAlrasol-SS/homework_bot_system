from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:submission_id>/approve/', views.ApproveSubmissionView.as_view(), name='approve-submission'),
    path('<int:submission_id>/reject/', views.RejectSubmissionView.as_view(), name='reject-submission'),
    path('pending/', views.PendingSubmissionsView.as_view(), name='pending-submissions'),
    path('my-submissions/', views.MySubmissionsView.as_view(), name='my-submissions'),
]