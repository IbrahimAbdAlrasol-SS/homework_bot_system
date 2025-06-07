from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class PointsHistory(BaseModel):
    """تاريخ النقاط"""
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='points_history',
        verbose_name='المستخدم'
    )
    
    points_change = models.IntegerField(
        verbose_name='تغيير النقاط'
    )
    
    reason = models.CharField(
        max_length=255,
        verbose_name='السبب'
    )
    
    total_points_after = models.IntegerField(
        verbose_name='إجمالي النقاط بعد التغيير'
    )
    
    assignment = models.ForeignKey(
        'assignments.Assignment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='الواجب المرتبط'
    )
    
    class Meta:
        verbose_name = 'تاريخ النقاط'
        verbose_name_plural = 'تاريخ النقاط'
        db_table = 'points_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.points_change} نقطة"


class DailyStatistics(BaseModel):
    """الإحصائيات اليومية"""
    
    date = models.DateField(
        verbose_name='التاريخ'
    )
    
    section = models.ForeignKey(
        'sections.Section',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='الشعبة'
    )
    
    total_assignments = models.IntegerField(
        default=0,
        verbose_name='إجمالي الواجبات'
    )
    
    total_submissions = models.IntegerField(
        default=0,
        verbose_name='إجمالي التسليمات'
    )
    
    approved_submissions = models.IntegerField(
        default=0,
        verbose_name='التسليمات المقبولة'
    )
    
    rejected_submissions = models.IntegerField(
        default=0,
        verbose_name='التسليمات المرفوضة'
    )
    
    late_submissions = models.IntegerField(
        default=0,
        verbose_name='التسليمات المتأخرة'
    )
    
    active_students = models.IntegerField(
        default=0,
        verbose_name='الطلاب النشطين'
    )
    
    average_points = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='متوسط النقاط'
    )
    
    class Meta:
        verbose_name = 'إحصائيات يومية'
        verbose_name_plural = 'الإحصائيات اليومية'
        db_table = 'daily_statistics'
        unique_together = ['date', 'section']
        ordering = ['-date']
    
    def __str__(self):
        section_name = self.section.name if self.section else "عام"
        return f"إحصائيات {section_name} - {self.date}"


class ActivityLog(BaseModel):
    """سجل الأنشطة"""
    
    class ActionType(models.TextChoices):
        LOGIN = 'login', 'تسجيل دخول'
        LOGOUT = 'logout', 'تسجيل خروج'
        SUBMIT_ASSIGNMENT = 'submit_assignment', 'تسليم واجب'
        APPROVE_SUBMISSION = 'approve_submission', 'قبول تسليم'
        REJECT_SUBMISSION = 'reject_submission', 'رفض تسليم'
        CREATE_ASSIGNMENT = 'create_assignment', 'إنشاء واجب'
        UPDATE_ASSIGNMENT = 'update_assignment', 'تحديث واجب'
        DELETE_ASSIGNMENT = 'delete_assignment', 'حذف واجب'
        ADD_POINTS = 'add_points', 'إضافة نقاط'
        SUBTRACT_POINTS = 'subtract_points', 'خصم نقاط'
        EARN_BADGE = 'earn_badge', 'كسب شارة'
        JOIN_COMPETITION = 'join_competition', 'انضمام لمسابقة'
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name='المستخدم'
    )
    
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        verbose_name='النشاط'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='عنوان IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='معلومات المتصفح'
    )
    
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات إضافية'
    )
    
    class Meta:
        verbose_name = 'سجل نشاط'
        verbose_name_plural = 'سجلات الأنشطة'
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_action_display()}"


class BotSession(BaseModel):
    """جلسات البوت"""
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='bot_sessions',
        verbose_name='المستخدم'
    )
    
    telegram_chat_id = models.BigIntegerField(
        verbose_name='معرف المحادثة'
    )
    
    session_data = models.JSONField(
        default=dict,
        verbose_name='بيانات الجلسة'
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='آخر نشاط'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    class Meta:
        verbose_name = 'جلسة بوت'
        verbose_name_plural = 'جلسات البوت'
        db_table = 'bot_sessions'
        unique_together = ['user', 'telegram_chat_id']
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"جلسة {self.user.get_full_name()}"


class RateLimit(BaseModel):
    """حدود المعدل"""
    
    identifier = models.CharField(
        max_length=255,
        verbose_name='المعرف',
        help_text='IP أو معرف المستخدم'
    )
    
    endpoint = models.CharField(
        max_length=255,
        verbose_name='نقطة النهاية'
    )
    
    request_count = models.IntegerField(
        default=0,
        verbose_name='عدد الطلبات'
    )
    
    window_start = models.DateTimeField(
        verbose_name='بداية النافزة الزمنية'
    )
    
    class Meta:
        verbose_name = 'حد المعدل'
        verbose_name_plural = 'حدود المعدل'
        db_table = 'rate_limits'
        unique_together = ['identifier', 'endpoint']
        indexes = [
            models.Index(fields=['identifier', 'endpoint']),
            models.Index(fields=['window_start']),
        ]
    
    def __str__(self):
        return f"{self.identifier} - {self.endpoint}"


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