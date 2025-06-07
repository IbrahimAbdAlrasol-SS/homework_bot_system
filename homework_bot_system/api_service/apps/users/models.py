# homework_bot_system/api_service/apps/users/models.py
# إصلاح المشكلة الحرجة - تعريف مكرر للكلاس

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.models import BaseModel


class User(AbstractUser, BaseModel):  # ✅ وراثة واحدة صحيحة
    """نموذج المستخدم المصحح"""
    
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
    
    # معرف التلكرام - مطلوب
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name='معرف التلكرام'
    )
    
    # الشعبة والدور
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
    
    # شخصية البوت
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
        verbose_name='رابط صورة الملف'
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
        return self.role in [self.Role.SUPER_ADMIN, self.Role.SECTION_ADMIN]
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def rank_title(self):
        """رتبة المستخدم حسب النقاط"""
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
        old_points = self.points
        self.points += points
        self.save(update_fields=['points'])
        
        # تسجيل العملية
        self._log_points_change(points, reason, self.points)
        
        # فحص الوصول لمستوى جديد
        self._check_level_up(old_points, self.points)
    
    def subtract_points(self, points, reason=""):
        """خصم نقاط من المستخدم"""
        old_points = self.points
        self.points = max(0, self.points - points)
        self.save(update_fields=['points'])
        
        # تسجيل العملية
        self._log_points_change(-points, reason, self.points)
    
    def update_penalty_counter(self, change):
        """تحديث عداد العقوبات"""
        old_counter = self.penalty_counter
        old_muted = self.is_muted
        
        self.penalty_counter = max(0, self.penalty_counter + change)
        self.is_muted = self.penalty_counter > 0
        
        self.save(update_fields=['penalty_counter', 'is_muted'])
        
        # إرسال إشعار عند تغيير حالة الكتم
        if old_muted != self.is_muted:
            self._send_penalty_notification()
    
    def _log_points_change(self, change, reason, total_after):
        """تسجيل تغيير النقاط"""
        try:
            from apps.analytics.models import PointsHistory
            PointsHistory.objects.create(
                user=self,
                points_change=change,
                reason=reason,
                total_points_after=total_after
            )
        except ImportError:
            pass  # التعامل مع عدم وجود النموذج
    
    def _check_level_up(self, old_points, new_points):
        """فحص الوصول لمستوى جديد"""
        old_level = self._get_level(old_points)
        new_level = self._get_level(new_points)
        
        if new_level > old_level:
            self._send_level_up_notification(new_level)
    
    def _get_level(self, points):
        """حساب المستوى حسب النقاط"""
        if points >= 100:
            return 4  # أسطورة
        elif points >= 51:
            return 3  # خبير
        elif points >= 21:
            return 2  # متقدم
        else:
            return 1  # مبتدئ
    
    def _send_penalty_notification(self):
        """إرسال إشعار عقوبة"""
        try:
            from apps.notifications.models import Notification
            
            if self.is_muted:
                Notification.objects.create(
                    user=self,
                    notification_type='penalty_applied',
                    title='تم كتم صوتك',
                    message=f'تم كتم صوتك بسبب العقوبات. العداد: {self.penalty_counter}'
                )
            else:
                Notification.objects.create(
                    user=self,
                    notification_type='penalty_applied',
                    title='تم رفع الكتم',
                    message='تم رفع الكتم عنك. يمكنك المشاركة بحرية.'
                )
        except ImportError:
            pass
    
    def _send_level_up_notification(self, level):
        """إرسال إشعار رفع المستوى"""
        try:
            from apps.notifications.models import Notification
            
            level_names = {1: 'مبتدئ', 2: 'متقدم', 3: 'خبير', 4: 'أسطورة'}
            level_name = level_names.get(level, 'غير معروف')
            
            Notification.objects.create(
                user=self,
                notification_type='points_awarded',
                title='🎉 مستوى جديد!',
                message=f'مبروك! وصلت إلى مستوى {level_name}'
            )
        except ImportError:
            pass