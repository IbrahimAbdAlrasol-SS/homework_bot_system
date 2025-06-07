from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import BaseModel

class Competition(BaseModel):
    """نموذج المسابقة المتقدم"""
    
    class Type(models.TextChoices):
        INDIVIDUAL = 'individual', 'فردية'
        SECTION = 'section', 'بين الشعب'
        MIXED = 'mixed', 'مختلطة'
    
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'قادمة'
        ACTIVE = 'active', 'نشطة'
        FINISHED = 'finished', 'منتهية'
        CANCELLED = 'cancelled', 'ملغية'
    
    class Period(models.TextChoices):
        DAILY = 'daily', 'يومية'
        WEEKLY = 'weekly', 'أسبوعية'
        MONTHLY = 'monthly', 'شهرية'
        SPECIAL = 'special', 'خاصة'
    
    title = models.CharField(max_length=200, verbose_name='عنوان المسابقة')
    description = models.TextField(verbose_name='وصف المسابقة')
    competition_type = models.CharField(max_length=20, choices=Type.choices, verbose_name='نوع المسابقة')
    period = models.CharField(max_length=20, choices=Period.choices, verbose_name='فترة المسابقة')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING, verbose_name='حالة المسابقة')
    
    start_date = models.DateTimeField(verbose_name='تاريخ البداية')
    end_date = models.DateTimeField(verbose_name='تاريخ النهاية')
    
    # إعدادات المشاركة
    sections = models.ManyToManyField('sections.Section', related_name='competitions', blank=True, verbose_name='الشعب المشاركة')
    max_participants = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)], verbose_name='الحد الأقصى للمشاركين')
    
    # نظام النقاط والجوائز
    early_submission_points = models.IntegerField(default=15, verbose_name='نقاط التسليم المبكر')
    on_time_points = models.IntegerField(default=10, verbose_name='نقاط التسليم في الوقت')
    late_penalty = models.IntegerField(default=5, verbose_name='عقوبة التأخير')
    
    prize_structure = models.JSONField(default=dict, verbose_name='هيكل الجوائز', help_text='مثال: {"1": 100, "2": 50, "3": 25}')
    
    # إعدادات متقدمة
    auto_ranking = models.BooleanField(default=True, verbose_name='ترتيب تلقائي')
    allow_voting = models.BooleanField(default=False, verbose_name='السماح بالتصويت')
    is_featured = models.BooleanField(default=False, verbose_name='مسابقة مميزة')
    
    class Meta:
        verbose_name = 'مسابقة'
        verbose_name_plural = 'المسابقات'
        db_table = 'competitions'
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_competition_type_display()})"
    
    @property
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.status == self.Status.ACTIVE
    
    @property
    def participant_count(self):
        return self.participants.count()

class CompetitionParticipant(BaseModel):
    """مشاركين المسابقة"""
    
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='participants', verbose_name='المسابقة')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='competition_participations', verbose_name='المستخدم')
    
    # النقاط والترتيب
    total_score = models.IntegerField(default=0, verbose_name='النتيجة الإجمالية')
    submission_score = models.IntegerField(default=0, verbose_name='نقاط التسليم')
    badge_score = models.IntegerField(default=0, verbose_name='نقاط الشارات')
    bonus_score = models.IntegerField(default=0, verbose_name='نقاط إضافية')
    
    rank = models.IntegerField(null=True, blank=True, verbose_name='الترتيب')
    previous_rank = models.IntegerField(null=True, blank=True, verbose_name='الترتيب السابق')
    
    # إحصائيات
    submissions_count = models.IntegerField(default=0, verbose_name='عدد التسليمات')
    early_submissions = models.IntegerField(default=0, verbose_name='التسليمات المبكرة')
    late_submissions = models.IntegerField(default=0, verbose_name='التسليمات المتأخرة')
    
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الانضمام')
    last_activity = models.DateTimeField(auto_now=True, verbose_name='آخر نشاط')
    
    class Meta:
        verbose_name = 'مشارك مسابقة'
        verbose_name_plural = 'مشاركين المسابقات'
        db_table = 'competition_participants'
        unique_together = ['competition', 'user']
        ordering = ['-total_score', 'joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.competition.title}"
    
    def calculate_total_score(self):
        """حساب النتيجة الإجمالية"""
        self.total_score = self.submission_score + self.badge_score + self.bonus_score
        self.save()
        return self.total_score

class SectionCompetition(BaseModel):
    """تنافس الشعب"""
    
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='section_battles', verbose_name='المسابقة')
    section = models.ForeignKey('sections.Section', on_delete=models.CASCADE, related_name='competitions', verbose_name='الشعبة')
    
    # نقاط الشعبة
    total_points = models.IntegerField(default=0, verbose_name='النقاط الإجمالية')
    average_score = models.FloatField(default=0.0, verbose_name='المتوسط')
    participant_count = models.IntegerField(default=0, verbose_name='عدد المشاركين')
    
    # ترتيب الشعبة
    rank = models.IntegerField(null=True, blank=True, verbose_name='ترتيب الشعبة')
    previous_rank = models.IntegerField(null=True, blank=True, verbose_name='الترتيب السابق')
    
    class Meta:
        verbose_name = 'تنافس شعبة'
        verbose_name_plural = 'تنافس الشعب'
        db_table = 'section_competitions'
        unique_together = ['competition', 'section']
        ordering = ['-total_points']
    
    def __str__(self):
        return f"{self.section.name} - {self.competition.title}"

class CompetitionRound(BaseModel):
    """جولات المسابقة"""
    
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='rounds', verbose_name='المسابقة')
    round_number = models.IntegerField(verbose_name='رقم الجولة')
    title = models.CharField(max_length=200, verbose_name='عنوان الجولة')
    description = models.TextField(blank=True, verbose_name='وصف الجولة')
    
    start_date = models.DateTimeField(verbose_name='تاريخ بداية الجولة')
    end_date = models.DateTimeField(verbose_name='تاريخ نهاية الجولة')
    
    points_multiplier = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(5.0)], verbose_name='مضاعف النقاط')
    
    class Meta:
        verbose_name = 'جولة مسابقة'
        verbose_name_plural = 'جولات المسابقات'
        db_table = 'competition_rounds'
        unique_together = ['competition', 'round_number']
        ordering = ['round_number']
    
    def __str__(self):
        return f"{self.competition.title} - الجولة {self.round_number}"

class CompetitionVote(BaseModel):
    """تصويت المسابقة"""
    
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='votes', verbose_name='المسابقة')
    voter = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='competition_votes', verbose_name='المصوت')
    candidate = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_votes', verbose_name='المرشح')
    
    vote_weight = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='وزن التصويت')
    comment = models.TextField(blank=True, verbose_name='تعليق')
    
    class Meta:
        verbose_name = 'تصويت مسابقة'
        verbose_name_plural = 'تصويتات المسابقات'
        db_table = 'competition_votes'
        unique_together = ['competition', 'voter', 'candidate']
    
    def __str__(self):
        return f"{self.voter.get_full_name()} صوت لـ {self.candidate.get_full_name()}"

class CompetitionReward(BaseModel):
    """جوائز المسابقة"""
    
    class RewardType(models.TextChoices):
        POINTS = 'points', 'نقاط'
        BADGE = 'badge', 'شارة'
        CERTIFICATE = 'certificate', 'شهادة'
        SPECIAL = 'special', 'جائزة خاصة'
    
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='rewards', verbose_name='المسابقة')
    participant = models.ForeignKey(CompetitionParticipant, on_delete=models.CASCADE, related_name='rewards', verbose_name='المشارك')
    
    reward_type = models.CharField(max_length=20, choices=RewardType.choices, verbose_name='نوع الجائزة')
    title = models.CharField(max_length=200, verbose_name='عنوان الجائزة')
    description = models.TextField(verbose_name='وصف الجائزة')
    
    points_value = models.IntegerField(default=0, verbose_name='قيمة النقاط')
    badge = models.ForeignKey('badges.Badge', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='الشارة')
    
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ منح الجائزة')
    
    class Meta:
        verbose_name = 'جائزة مسابقة'
        verbose_name_plural = 'جوائز المسابقات'
        db_table = 'competition_rewards'
    
    def __str__(self):
        return f"{self.title} - {self.participant.user.get_full_name()}"