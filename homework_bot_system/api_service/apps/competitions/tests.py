from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Competition, CompetitionParticipant
from apps.sections.models import Section

User = get_user_model()

class CompetitionModelTest(TestCase):
    def setUp(self):
        self.competition = Competition.objects.create(
            title='مسابقة تجريبية',
            description='وصف المسابقة',
            competition_type=Competition.Type.INDIVIDUAL,
            period=Competition.Period.WEEKLY,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8)
        )
    
    def test_competition_creation(self):
        self.assertEqual(self.competition.title, 'مسابقة تجريبية')
        self.assertEqual(self.competition.status, Competition.Status.UPCOMING)
    
    def test_is_active_property(self):
        # المسابقة لم تبدأ بعد
        self.assertFalse(self.competition.is_active)
        
        # تفعيل المسابقة
        self.competition.start_date = timezone.now() - timedelta(hours=1)
        self.competition.status = Competition.Status.ACTIVE
        self.competition.save()
        
        self.assertTrue(self.competition.is_active)

class CompetitionAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.section = Section.objects.create(
            name='الشعبة الأولى',
            code='SEC001'
        )
        
        self.competition = Competition.objects.create(
            title='مسابقة API',
            description='اختبار API',
            competition_type=Competition.Type.INDIVIDUAL,
            period=Competition.Period.WEEKLY,
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=8)
        )
    
    def test_list_competitions(self):
        response = self.client.get('/api/v1/competitions/competitions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_join_competition(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/competitions/competitions/{self.competition.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # التحقق من إنشاء المشاركة
        self.assertTrue(
            CompetitionParticipant.objects.filter(
                competition=self.competition,
                user=self.user
            ).exists()
        )
    
    def test_join_competition_twice(self):
        self.client.force_authenticate(user=self.user)
        
        # الانضمام الأول
        self.client.post(f'/api/v1/competitions/competitions/{self.competition.id}/join/')
        
        # محاولة الانضمام مرة أخرى
        response = self.client.post(f'/api/v1/competitions/competitions/{self.competition.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)