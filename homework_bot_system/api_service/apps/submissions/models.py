from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel


class Submission(BaseModel):
    """نموذج التسليم"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'في الانتظار'
        APPROVED = 'approved', 'مقبول'
        REJECTED = 'rejected', 'مرفوض'
        NEEDS_REVISION = 'needs_revision', 'يحتاج مراجعة'
    
    class Grade(models.TextChoices):
        EXCELLENT = 'excellent', 'ممتاز'
        VERY_GOOD = 'very_good', 'جيد جداً'
        GOOD = 'good', 'جيد'
        ACCEPTABLE = 'acceptable', 'مقبول'
        POOR = 'poor', 'ضعيف'
    
    assignment = models.ForeignKey(
        'assignments.Assignment',
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='الواجب'
    )
    
    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'role': 'student'},
        verbose_name='الطالب'
    )
    
    content = models.TextField(
        blank=True,
        verbose_name='محتوى التسليم'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='الحالة'
    )
    
    grade = models.CharField(
        max_length=20,
        choices=Grade.choices,
        null=True,
        blank=True,
        verbose_name='التقدير'
    )
    
    points_earned = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='النقاط المكتسبة'
    )
    
    is_late = models.BooleanField(
        default=False,
        verbose_name='متأخر'
    )
    
    is_excellent = models.BooleanField(
        default=False,
        verbose_name='متميز'
    )
    
    reviewed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions',
        verbose_name='تمت المراجعة بواسطة'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت المراجعة'
    )
    
    feedback = models.TextField(
        blank=True,
        verbose_name='التعليقات'
    )
    
    telegram_message_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='معرف رسالة التلكرام'
    )
    
    class Meta:
        verbose_name = 'تسليم'
        verbose_name_plural = 'التسليمات'
        db_table = 'submissions'
        ordering = ['-created_at']
        unique_together = ['assignment', 'student']
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student']),
            models.Index(fields=['status']),
            models.Index(fields=['is_late']),
            models.Index(fields=['is_excellent']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        # تحديد إذا كان التسليم متأخر
        if not self.pk:  # تسليم جديد
            self.is_late = timezone.now() > self.assignment.deadline
        
        super().save(*args, **kwargs)
    
    def approve(self, reviewed_by, feedback="", is_excellent=False):
        """قبول التسليم"""
        self.status = self.Status.APPROVED
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.feedback = feedback
        self.is_excellent = is_excellent
        
        # حساب النقاط
        self.points_earned = self.assignment.calculate_points(
            is_late=self.is_late,
            is_excellent=is_excellent
        )
        
        self.save()
        
        # إضافة النقاط للطالب
        self.student.add_points(
            self.points_earned,
            f"تسليم واجب: {self.assignment.title}"
        )
        
        # تحديث سلسلة التسليم
        self.student.submission_streak += 1
        self.student.save(update_fields=['submission_streak'])
    
    def reject(self, reviewed_by, feedback):
        """رفض التسليم"""
        self.status = self.Status.REJECTED
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.feedback = feedback
        self.points_earned = 0
        
        self.save()
        
        # إضافة عقوبة للطالب
        self.student.subtract_points(
            self.assignment.penalty_points,
            f"رفض تسليم واجب: {self.assignment.title}"
        )
        
        # كسر سلسلة التسليم
        self.student.submission_streak = 0
        self.student.save(update_fields=['submission_streak'])
    
    def request_revision(self, reviewed_by, feedback):
        """طلب مراجعة"""
        self.status = self.Status.NEEDS_REVISION
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.feedback = feedback
        
        self.save()


class SubmissionFile(BaseModel):
    """ملفات التسليم"""
    
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='التسليم'
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
        verbose_name = 'ملف تسليم'
        verbose_name_plural = 'ملفات التسليمات'
        db_table = 'submission_files'
    
    def __str__(self):
        return f"{self.file_name} - {self.submission}"


class SubmissionComment(BaseModel):
    """تعليقات التسليم"""
    
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='التسليم'
    )
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='المستخدم'
    )
    
    content = models.TextField(
        verbose_name='المحتوى'
    )
    
    is_private = models.BooleanField(
        default=False,
        verbose_name='خاص'
    )
    
    class Meta:
        verbose_name = 'تعليق تسليم'
        verbose_name_plural = 'تعليقات التسليمات'
        db_table = 'submission_comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"تعليق {self.user.get_full_name()} على {self.submission}"