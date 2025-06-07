
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel


class Assignment(BaseModel):
    """نموذج الواجب المصحح"""
    
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
    
    # إضافة حقل المادة المفقود
    subject = models.CharField(
        max_length=100,
        verbose_name='المادة',
        help_text='اسم المادة الدراسية'
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
    
    # إصلاح تضارب الأسماء - استخدام due_date بدلاً من deadline
    due_date = models.DateTimeField(
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
    
    # نظام النقاط المحسن
    points_value = models.IntegerField(  # ✅ توحيد الاسم
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name='نقاط الواجب'
    )
    
    excellence_points = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name='نقاط التميز'
    )
    
    penalty_points = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        verbose_name='نقاط العقوبة'
    )
    
    # إضافة حقل الحد الأقصى للتسليمات
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
        verbose_name='نسبة عقوبة التأخير (%)'
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
            models.Index(fields=['due_date']),  # ✅ إصلاح الفهرس
            models.Index(fields=['priority']),
            models.Index(fields=['created_by']),
            models.Index(fields=['subject']),
        ]
    
    @property
    def is_overdue(self):
        """تحقق من انتهاء الموعد النهائي"""
        return timezone.now() > self.due_date  # ✅ إصلاح الاسم
    
    @property
    def time_remaining(self):
        """الوقت المتبقي للموعد النهائي"""
        if self.is_overdue:
            return None
        return self.due_date - timezone.now()  # ✅ إصلاح الاسم
    
    def days_until_due(self):
        """عدد الأيام حتى الموعد النهائي"""
        if self.is_overdue:
            return 0
        
        time_diff = self.due_date - timezone.now()  # ✅ إصلاح الاسم
        return time_diff.days
    
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
        
        return (self.submission_count / total_students) * 100
    
    def get_student_submission(self, student):
        """الحصول على تسليم الطالب"""
        return self.submissions.filter(student=student).first()
    
    def can_submit(self, student):
        """تحقق من إمكانية التسليم - محسن"""
        # فحص حالة الواجب
        if self.status != self.Status.PUBLISHED:
            return False, "الواجب غير منشور"
        
        # فحص الموعد النهائي
        if not self.allow_late_submission and self.is_overdue:
            return False, "انتهى الموعد النهائي"
        
        # فحص عدد التسليمات
        student_submissions = self.submissions.filter(student=student).count()
        if student_submissions >= self.max_submissions:
            return False, f"تم الوصول للحد الأقصى من التسليمات ({self.max_submissions})"
        
        # فحص حالة الطالب
        if student.is_muted:
            return False, "لا يمكنك التسليم بسبب الكتم"
        
        return True, "يمكن التسليم"
    
    def calculate_points(self, is_late=False, is_excellent=False):
        """حساب النقاط للتسليم - محسن"""
        points = self.points_value  # ✅ استخدام الاسم الموحد
        
        # إضافة نقاط التميز
        if is_excellent:
            points += self.excellence_points
        
        # خصم نقاط التأخير
        if is_late and self.allow_late_submission:
            penalty = (points * self.late_penalty_percentage) // 100
            points = max(0, points - penalty)
        
        return points
    
    def get_priority_emoji(self):
        """الحصول على رمز الأولوية"""
        emojis = {
            'low': '🟢',
            'medium': '🟡', 
            'high': '🔴',
            'urgent': '🚨'
        }
        return emojis.get(self.priority, '⚪')


