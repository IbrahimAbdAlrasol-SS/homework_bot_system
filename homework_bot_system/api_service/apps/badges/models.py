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


class Competition(BaseModel):
    """نموذج المسابقة"""
    
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'قادمة'
        ACTIVE = 'active', 'نشطة'
        ENDED = 'ended', 'انتهت'
    
    class Type(models.TextChoices):
        DAILY = 'daily', 'يومية'
        WEEKLY = 'weekly', 'أسبوعية'
        MONTHLY = 'monthly', 'شهرية'
        SPECIAL = 'special', 'خاصة'
    
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان المسابقة'
    )
    
    description = models.TextField(
        verbose_name='وصف المسابقة'
    )
    
    competition_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        verbose_name='نوع المسابقة'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPCOMING,
        verbose_name='حالة المسابقة'
    )
    
    start_date = models.DateTimeField(
        verbose_name='تاريخ البداية'
    )
    
    end_date = models.DateTimeField(
        verbose_name='تاريخ النهاية'
    )
    
    sections = models.ManyToManyField(
        'sections.Section',
        related_name='competitions',
        blank=True,
        verbose_name='الشعب المشاركة'
    )
    
    prize_points = models.JSONField(
        default=dict,
        verbose_name='نقاط الجوائز',
        help_text='مثال: {"1": 100, "2": 50, "3": 25}'
    )
    
    max_participants = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        verbose_name='الحد الأقصى للمشاركين'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    
    class Meta:
        verbose_name = 'مسابقة'
        verbose_name_plural = 'المسابقات'
        db_table = 'competitions'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_competition_type_display()})"
    
    @property
    def participant_count(self):
        """عدد المشاركين"""
        return self.participants.count()
    
    @property
    def is_full(self):
        """تحقق من امتلاء المسابقة"""
        if not self.max_participants:
            return False
        return self.participant_count >= self.max_participants


class CompetitionParticipant(BaseModel):
    """مشاركين المسابقة"""
    
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='المسابقة'
    )
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='competition_participations',
        verbose_name='المستخدم'
    )
    
    score = models.IntegerField(
        default=0,
        verbose_name='النتيجة'
    )
    
    rank = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='الترتيب'
    )
    
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الانضمام'
    )
    
    class Meta:
        verbose_name = 'مشارك مسابقة'
        verbose_name_plural = 'مشاركين المسابقات'
        db_table = 'competition_participants'
        unique_together = ['competition', 'user']
        ordering = ['-score']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.competition.title}"