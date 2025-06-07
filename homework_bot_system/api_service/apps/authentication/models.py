from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import BaseModel
import secrets

User = get_user_model()


class APIKey(BaseModel):
    """مفاتيح API للوصول الخارجي"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='اسم المفتاح'
    )
    
    key = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='المفتاح'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name='المستخدم'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الانتهاء'
    )
    
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخر استخدام'
    )
    
    permissions = models.JSONField(
        default=list,
        verbose_name='الصلاحيات'
    )
    
    class Meta:
        verbose_name = 'مفتاح API'
        verbose_name_plural = 'مفاتيح API'
        db_table = 'api_keys'
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    @property
    def is_expired(self):
        """تحقق من انتهاء صلاحية المفتاح"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def update_last_used(self):
        """تحديث وقت آخر استخدام"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class LoginSession(BaseModel):
    """جلسات تسجيل الدخول"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_sessions',
        verbose_name='المستخدم'
    )
    
    session_token = models.CharField(
        max_length=128,
        unique=True,
        verbose_name='رمز الجلسة'
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name='عنوان IP'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='معلومات المتصفح'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    expires_at = models.DateTimeField(
        verbose_name='تاريخ الانتهاء'
    )
    
    last_activity = models.DateTimeField(
        default=timezone.now,
        verbose_name='آخر نشاط'
    )
    
    class Meta:
        verbose_name = 'جلسة تسجيل دخول'
        verbose_name_plural = 'جلسات تسجيل الدخول'
        db_table = 'login_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_token']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(64)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"
    
    @property
    def is_expired(self):
        """تحقق من انتهاء صلاحية الجلسة"""
        return timezone.now() > self.expires_at
    
    def extend_session(self, hours=24):
        """تمديد الجلسة"""
        self.expires_at = timezone.now() + timezone.timedelta(hours=hours)
        self.last_activity = timezone.now()
        self.save(update_fields=['expires_at', 'last_activity'])
    
    def deactivate(self):
        """إلغاء تفعيل الجلسة"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class PasswordResetToken(BaseModel):
    """رموز إعادة تعيين كلمة المرور"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name='المستخدم'
    )
    
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='الرمز'
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name='مستخدم'
    )
    
    expires_at = models.DateTimeField(
        verbose_name='تاريخ الانتهاء'
    )
    
    class Meta:
        verbose_name = 'رمز إعادة تعيين كلمة المرور'
        verbose_name_plural = 'رموز إعادة تعيين كلمة المرور'
        db_table = 'password_reset_tokens'
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    @property
    def is_expired(self):
        """تحقق من انتهاء صلاحية الرمز"""
        return timezone.now() > self.expires_at
    
    def use_token(self):
        """استخدام الرمز"""
        self.is_used = True
        self.save(update_fields=['is_used'])