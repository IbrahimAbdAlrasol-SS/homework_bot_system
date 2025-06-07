from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class Badge(BaseModel):
    """نموذج الشارة"""
    
    class Type(models.TextChoices):
        ACHIEVEMENT = 'achievement', 'إنجاز'
        STREAK = 'streak', 'سلسلة'
        POINTS = 'points', 'نقاط'
        SPECIAL = 'special', 'خاص'
    
    class Rarity(models.TextChoices):
        COMMON = 'common', 'عادي'
        RARE = 'rare', 'نادر'
        EPIC = 'epic', 'ملحمي'
        LEGENDARY = 'legendary', 'أسطوري'
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='اسم الشارة'
    )
    
    description = models.TextField(
        verbose_name='وصف الشارة'
    )
    
    icon = models.CharField(
        max_length=10,
        verbose_name='أيقونة الشارة'
    )
    
    badge_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        verbose_name='نوع الشارة'
    )
    
    rarity = models.CharField(
        max_length=20,
        choices=Rarity.choices,
        default=Rarity.COMMON,
        verbose_name='ندرة الشارة'
    )
    
    points_required = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='النقاط المطلوبة'
    )
    
    streak_required = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='السلسلة المطلوبة'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    class Meta:
        verbose_name = 'شارة'
        verbose_name_plural = 'الشارات'
        db_table = 'badges'
        ordering = ['rarity', 'name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(BaseModel):
    """شارات المستخدم"""
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='badges',
        verbose_name='المستخدم'
    )
    
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        verbose_name='الشارة'
    )
    
    earned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الحصول'
    )
    
    class Meta:
        verbose_name = 'شارة مستخدم'
        verbose_name_plural = 'شارات المستخدمين'
        db_table = 'user_badges'
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.badge.name}"
