from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel, SoftDeleteModel


class Assignment(SoftDeleteModel):
    """نموذج الواجب"""
    
    class Priority(models.TextChoices):
        LOW = 'low', 'منخفضة'
        MEDIUM = 'medium', 'متوسطة'
        HIGH = 'high', 'عالية'
        URGENT = 'urgent', 'عاجلة'
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'مسودة'
        PUBLISHED = 'published', 'منشور'
        CLOSED = 'closed', 'مغلق'
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان الواجب'
    )
    
    description = models.TextField(
        verbose_name='وصف الواجب'
    )
    
    section = models.ForeignKey(
        'sections.Section',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='الشعبة'
    )
    
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='created_assignments',
        verbose_name='منشئ الواجب'
    )
    
    deadline = models.DateTimeField(
        verbose_name='الموعد النهائي'
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name='الأولوية'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='الحالة'
    )
    
    points_reward = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='نقاط المكافأة'
    )
    
    excellence_points = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name='نقاط التميز'
    )
    
    penalty_points = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        verbose_name='نقاط العقوبة'
    )
    
    max_submissions = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='الحد الأقصى للتسليمات'
    )
    
    allow_late_submission = models.BooleanField(
        default=False,
        verbose_name='السماح بالتسليم المتأخر'
    )
    
    late_penalty_percentage = models.IntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='نسبة عقوبة التأخير'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    telegram_message_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='معرف رسالة التلكرام'
    )
    
    class Meta:
        verbose_name = 'واجب'
        verbose_name_plural = 'الواجبات'
        db_table = 'assignments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['section', 'status']),
            models.Index(fields=['deadline']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.section.name}"
    
    @property
    def is_overdue(self):
        """تحقق من انتهاء الموعد النهائي"""
        return timezone.now() > self.deadline
    
    @property
    def time_remaining(self):
        """الوقت المتبقي للموعد النهائي"""
        if self.is_overdue:
            return None
        return self.deadline - timezone.now()
    
    @property
    def submission_count(self):
        """عدد التسليمات"""
        return self.submissions.count()
    
    @property
    def approved_submission_count(self):
        """عدد التسليمات المقبولة"""
        return self.submissions.filter(status='approved').count()
    
    @property
    def submission_rate(self):
        """معدل التسليم"""
        total_students = self.section.students.filter(
            status='active',
            role='student'
        ).count()
        
        if total_students == 0:
            return 0
        
        return (self.approved_submission_count / total_students) * 100
    
    def get_student_submission(self, student):
        """الحصول على تسليم الطالب"""
        return self.submissions.filter(student=student).first()
    
    def can_submit(self, student):
        """تحقق من إمكانية التسليم"""
        if self.status != self.Status.PUBLISHED:
            return False, "الواجب غير منشور"
        
        if not self.allow_late_submission and self.is_overdue:
            return False, "انتهى الموعد النهائي"
        
        student_submissions = self.submissions.filter(student=student).count()
        if student_submissions >= self.max_submissions:
            return False, "تم الوصول للحد الأقصى من التسليمات"
        
        return True, "يمكن التسليم"
    
    def calculate_points(self, is_late=False, is_excellent=False):
        """حساب النقاط للتسليم"""
        points = self.points_reward
        
        if is_excellent:
            points += self.excellence_points
        
        if is_late and self.allow_late_submission:
            penalty = (points * self.late_penalty_percentage) // 100
            points -= penalty
        
        return max(0, points)


class AssignmentFile(BaseModel):
    """ملفات الواجب"""
    
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='الواجب'
    )
    
    file_name = models.CharField(
        max_length=255,
        verbose_name='اسم الملف'
    )
    
    file_url = models.URLField(
        max_length=500,
        verbose_name='رابط الملف'
    )
    
    file_size = models.BigIntegerField(
        verbose_name='حجم الملف بالبايت'
    )
    
    file_type = models.CharField(
        max_length=50,
        verbose_name='نوع الملف'
    )
    
    telegram_file_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='معرف ملف التلكرام'
    )
    
    class Meta:
        verbose_name = 'ملف واجب'
        verbose_name_plural = 'ملفات الواجبات'
        db_table = 'assignment_files'
    
    def __str__(self):
        return f"{self.file_name} - {self.assignment.title}"