from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.sections.models import Section
from .models import Assignment

User = get_user_model()

class AssignmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            telegram_id=123456789
        )
        self.section = Section.objects.create(
            name='Test Section',
            study_type='morning'
        )
    
    def test_assignment_creation(self):
        assignment = Assignment.objects.create(
            title='Test Assignment',
            description='Test Description',
            subject='Math',
            section=self.section,
            created_by=self.user,
            deadline=timezone.now() + timedelta(days=7)
        )
        
        self.assertEqual(assignment.title, 'Test Assignment')
        self.assertFalse(assignment.is_overdue)