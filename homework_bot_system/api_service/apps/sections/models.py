from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel, SoftDeleteModel


class Section(SoftDeleteModel):
    """نموذج الشعبة الدراسية"""
    
    class StudyType(models.TextChoices):
        MORNING = 'morning', 'صباحي'
        EVENING = 'evening', 'مسائي'
    
    name = models.CharField(
        max_length=100,
        verbose_name='اسم الشعبة'
    )
    
    study_type = models.CharField(
        max_length=20,
        choices=StudyType.choices,
        verbose_name='نوع الدراسة'
    )
    
    admin = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_sections',
        limit_choices_to={'role': 'section_admin'},
        verbose_name='أدمن الشعبة'
    )
    
    telegram_group_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='معرف مجموعة التلكرام'
    )
    
    storage_group_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='معرف مجموعة التخزين'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    max_students = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1)],
        verbose_name='الحد الأقصى للطلاب'
    )
    
    class Meta:
        verbose_name = 'شعبة'
        verbose_name_plural = 'الشعب'
        db_table = 'sections'
        unique_together = ['name', 'study_type']
        indexes = [
            models.Index(fields=['study_type', 'is_active']),
            models.Index(fields=['admin']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_study_type_display()}"
    
    @property
    def student_count(self):
        """عدد الطلاب في الشعبة"""
        return self.students.filter(status='active').count()
    
    @property
    def is_full(self):
        """تحقق من امتلاء الشعبة"""
        return self.student_count >= self.max_students
    
    def get_active_assignments(self):
        """الحصول على الواجبات النشطة"""
        from django.utils import timezone
        return self.assignments.filter(
            is_active=True,
            deadline__gte=timezone.now()
        ).order_by('deadline')
    
    def get_section_ranking(self):
        """ترتيب طلاب الشعبة حسب النقاط"""
        return self.students.filter(
            status='active',
            role='student'
        ).order_by('-points', '-submission_streak')
    
    def calculate_section_stats(self):
        """حساب إحصائيات الشعبة"""
        students = self.students.filter(status='active', role='student')
        
        if not students.exists():
            return {
                'total_students': 0,
                'average_points': 0,
                'top_student': None,
                'submission_rate': 0
            }
        
        total_points = sum(student.points for student in students)
        average_points = total_points / students.count()
        top_student = students.order_by('-points').first()
        
        # حساب معدل التسليم
        from apps.assignments.models import Assignment
        from apps.submissions.models import Submission
        
        total_assignments = Assignment.objects.filter(
            section=self,
            is_active=True
        ).count()
        
        if total_assignments > 0:
            total_submissions = Submission.objects.filter(
                assignment__section=self,
                status='approved'
            ).count()
            submission_rate = (total_submissions / (total_assignments * students.count())) * 100
        else:
            submission_rate = 0
        
        return {
            'total_students': students.count(),
            'average_points': round(average_points, 2),
            'top_student': top_student,
            'submission_rate': round(submission_rate, 2)
        }