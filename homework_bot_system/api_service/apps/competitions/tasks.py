from celery import shared_task
from django.utils import timezone
from .models import Competition
from .utils import CompetitionCalculator, CompetitionRewardManager

@shared_task
def update_competition_status():
    """تحديث حالة المسابقات تلقائياً"""
    now = timezone.now()
    
    # تفعيل المسابقات القادمة
    upcoming_competitions = Competition.objects.filter(
        status=Competition.Status.UPCOMING,
        start_date__lte=now
    )
    
    for competition in upcoming_competitions:
        competition.status = Competition.Status.ACTIVE
        competition.save()
    
    # إنهاء المسابقات النشطة
    active_competitions = Competition.objects.filter(
        status=Competition.Status.ACTIVE,
        end_date__lte=now
    )
    
    for competition in active_competitions:
        competition.status = Competition.Status.FINISHED
        competition.save()
        
        # منح الجوائز تلقائياً
        CompetitionRewardManager.award_competition_prizes(competition)
    
    return f"تم تحديث {upcoming_competitions.count() + active_competitions.count()} مسابقة"

@shared_task
def update_competition_rankings():
    """تحديث ترتيب المسابقات النشطة"""
    active_competitions = Competition.objects.filter(
        status=Competition.Status.ACTIVE,
        auto_ranking=True
    )
    
    updated_count = 0
    for competition in active_competitions:
        CompetitionCalculator.update_participant_scores(competition)
        CompetitionCalculator.update_participant_rankings(competition)
        
        if competition.competition_type in [Competition.Type.SECTION, Competition.Type.MIXED]:
            CompetitionCalculator.update_section_rankings(competition)
        
        updated_count += 1
    
    return f"تم تحديث ترتيب {updated_count} مسابقة"

@shared_task
def calculate_daily_competition_stats():
    """حساب إحصائيات المسابقات اليومية"""
    from .utils import CompetitionAnalytics
    
    stats = CompetitionAnalytics.get_general_stats()
    
    # يمكن حفظ الإحصائيات في قاعدة البيانات أو إرسالها للتحليلات
    return f"تم حساب إحصائيات {stats['total_competitions']} مسابقة"