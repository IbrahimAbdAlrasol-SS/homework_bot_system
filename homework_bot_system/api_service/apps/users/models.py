from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel


class User(AbstractUser, BaseModel):
    """نموذج المستخدم المخصص"""
    
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'مسؤول عام'
        SECTION_ADMIN = 'section_admin', 'أدمن شعبة'
        STUDENT = 'student', 'طالب'
    
    class Personality(models.TextChoices):
        SERIOUS = 'serious', 'جدي'
        FRIENDLY = 'friendly', 'ودود'
        MOTIVATOR = 'motivator', 'محفز'
        SARCASTIC = 'sarcastic', 'ساخر'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'نشط'
        INACTIVE = 'inactive', 'غير نشط'
        BANNED = 'banned', 'محظور'
    
    # معلومات التلكرام
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name='معرف التلكرام',
        help_text='معرف المستخدم الفريد في التلكرام'
    )
    
    # معلومات الشعبة والدور
    section = models.ForeignKey(
        'sections.Section',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='الشعبة'
    )
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='الدور'
    )
    
    # إعدادات البوت
    personality = models.CharField(
        max_length=20,
        choices=Personality.choices,
        default=Personality.FRIENDLY,
        verbose_name='شخصية البوت'
    )
    
    # نظام النقاط
    points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='النقاط'
    )
    
    penalty_counter = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='عداد العقوبات'
    )
    
    excellence_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='نقاط التميز'
    )
    
    submission_streak = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='سلسلة التسليم'
    )
    
    # حالة الكتم
    is_muted = models.BooleanField(
        default=False,
        verbose_name='مكتوم'
    )
    
    # معلومات إضافية
    profile_photo_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='رابط صورة الملف الشخصي'
    )
    
    last_activity = models.DateTimeField(
        default=timezone.now,
        verbose_name='آخر نشاط'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='الحالة'
    )
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        db_table = 'users'
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['section', 'role']),
            models.Index(fields=['status']),
            models.Index(fields=['points']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """تحقق من كون المستخدم أدمن"""
        return self.role in [self.Role.SUPER_ADMIN, self.Role.SECTION_ADMIN]
    
    @property
    def is_student(self):
        """تحقق من كون المستخدم طالب"""
        return self.role == self.Role.STUDENT
    
    @property
    def rank_title(self):
        """حساب الرتبة حسب النقاط"""
        if self.points >= 100:
            return '👑 أسطورة'
        elif self.points >= 51:
            return '🥇 خبير'
        elif self.points >= 21:
            return '🥈 متقدم'
        else:
            return '🥉 مبتدئ'
    
    def update_activity(self):
        """تحديث وقت آخر نشاط"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def add_points(self, points, reason=""):
        """إضافة نقاط للمستخدم"""
        self.points += points
        self.save(update_fields=['points'])
        
        # تسجيل العملية
        from apps.analytics.models import PointsHistory
        PointsHistory.objects.create(
            user=self,
            points_change=points,
            reason=reason,
            total_points_after=self.points
        )
    
    def subtract_points(self, points, reason=""):
        """خصم نقاط من المستخدم"""
        self.points = max(0, self.points - points)
        self.save(update_fields=['points'])
        
        # تسجيل العملية
        from apps.analytics.models import PointsHistory
        PointsHistory.objects.create(
            user=self,
            points_change=-points,
            reason=reason,
            total_points_after=self.points
        )
    
    def increment_penalty(self):
        """زيادة عداد العقوبات"""
        self.penalty_counter += 1
        self.is_muted = self.penalty_counter > 0
        self.save(update_fields=['penalty_counter', 'is_muted'])
    
    def decrement_penalty(self):
        """تقليل عداد العقوبات"""
        self.penalty_counter = max(0, self.penalty_counter - 1)
        self.is_muted = self.penalty_counter > 0
        self.save(update_fields=['penalty_counter', 'is_muted'])
    
    # إضافة منطق العداد الذكي
    class User(AbstractUser):
        def update_penalty_counter(self, change):
            """تحديث عداد العقوبات بذكاء"""
            self.penalty_counter = max(0, self.penalty_counter + change)
            self.is_muted = self.penalty_counter > 0
            self.save()
            
            # إرسال إشعار إذا تم كتم الصوت
            if self.is_muted and change > 0:
                from apps.notifications.models import Notification
                Notification.objects.create(
                    user=self,
                    notification_type='penalty',
                    title='تم كتم صوتك',
                    message=f'تم كتم صوتك بسبب تجاوز حد العقوبات ({self.penalty_counter})'
                )