from django.db import models
from core.models import BaseModel

class Notification(BaseModel):
    """الإشعارات"""
    
    class Type(models.TextChoices):
        ASSIGNMENT_REMINDER = 'assignment_reminder', 'تذكير واجب'
        DEADLINE_WARNING = 'deadline_warning', 'تحذير موعد نهائي'
        SUBMISSION_APPROVED = 'submission_approved', 'تسليم مقبول'
        SUBMISSION_REJECTED = 'submission_rejected', 'تسليم مرفوض'
        BADGE_EARNED = 'badge_earned', 'شارة مكتسبة'
        COMPETITION_UPDATE = 'competition_update', 'تحديث مسابقة'
        PENALTY_APPLIED = 'penalty_applied', 'عقوبة مطبقة'
        POINTS_AWARDED = 'points_awarded', 'نقاط ممنوحة'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'في الانتظار'
        SENT = 'sent', 'مرسل'
        FAILED = 'failed', 'فشل'
        READ = 'read', 'مقروء'
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستخدم'
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=Type.choices,
        verbose_name='نوع الإشعار'
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name='العنوان'
    )
    
    message = models.TextField(
        verbose_name='الرسالة'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='الحالة'
    )
    
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='موعد الإرسال'
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت الإرسال'
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='وقت القراءة'
    )
    
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات إضافية'
    )
    
    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"