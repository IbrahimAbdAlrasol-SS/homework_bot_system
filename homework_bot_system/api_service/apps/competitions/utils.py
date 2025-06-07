from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from .models import Competition, CompetitionParticipant, SectionCompetition
from apps.submissions.models import Submission
from apps.badges.models import UserBadge

class CompetitionCalculator:
    """حاسبة نقاط ومراتب المسابقات"""
    
    @staticmethod
    def calculate_participant_score(participant):
        """حساب نقاط المشارك"""
        user = participant.user
        competition = participant.competition
        
        # نقاط التسليمات
        submission_score = CompetitionCalculator._calculate_submission_score(
            user, competition
        )
        
        # نقاط الشارات
        badge_score = CompetitionCalculator._calculate_badge_score(
            user, competition
        )
        
        # تحديث النقاط
        participant.submission_score = submission_score
        participant.badge_score = badge_score
        participant.total_score = submission_score + badge_score + participant.bonus_score
        participant.save()
        
        return participant.total_score
    
    @staticmethod
    def _calculate_submission_score(user, competition):
        """حساب نقاط التسليمات"""
        submissions = Submission.objects.filter(
            user=user,
            assignment__sections__competitions=competition,
            created_at__range=[competition.start_date, competition.end_date]
        )
        
        total_score = 0
        early_count = 0
        late_count = 0
        
        for submission in submissions:
            assignment = submission.assignment
            submission_time = submission.created_at
            
            # تحديد نوع التسليم
            if submission_time <= assignment.due_date:
                # تسليم في الوقت أو مبكر
                days_early = (assignment.due_date - submission_time).days
                if days_early >= 1:  # تسليم مبكر
                    total_score += competition.early_submission_points
                    early_count += 1
                else:  # تسليم في الوقت
                    total_score += competition.on_time_points
            else:
                # تسليم متأخر
                total_score -= competition.late_penalty
                late_count += 1
        
        # تحديث إحصائيات المشارك
        participant = CompetitionParticipant.objects.get(
            user=user, competition=competition
        )
        participant.submissions_count = submissions.count()
        participant.early_submissions = early_count
        participant.late_submissions = late_count
        participant.save()
        
        return max(0, total_score)  # لا تقل النقاط عن صفر
    
    @staticmethod
    def _calculate_badge_score(user, competition):
        """حساب نقاط الشارات"""
        user_badges = UserBadge.objects.filter(
            user=user,
            earned_at__range=[competition.start_date, competition.end_date]
        )
        
        total_score = 0
        for user_badge in user_badges:
            badge = user_badge.badge
            # نقاط مختلفة حسب نوع الشارة
            if badge.badge_type == 'gold':
                total_score += 50
            elif badge.badge_type == 'silver':
                total_score += 30
            elif badge.badge_type == 'bronze':
                total_score += 20
            else:
                total_score += 10
        
        return total_score
    
    @staticmethod
    def update_rankings(competition):
        """تحديث ترتيب المشاركين"""
        participants = competition.participants.order_by('-total_score', 'joined_at')
        
        for index, participant in enumerate(participants, 1):
            participant.previous_rank = participant.rank
            participant.rank = index
            participant.save()
    
    @staticmethod
    def update_section_rankings(competition):
        """تحديث ترتيب الشعب"""
        section_competitions = competition.section_battles.all()
        
        for section_comp in section_competitions:
            # حساب نقاط الشعبة
            participants = competition.participants.filter(
                user__section=section_comp.section
            )
            
            total_points = participants.aggregate(
                total=Sum('total_score')
            )['total'] or 0
            
            average_score = participants.aggregate(
                avg=Avg('total_score')
            )['avg'] or 0
            
            participant_count = participants.count()
            
            section_comp.total_points = total_points
            section_comp.average_score = round(average_score, 2)
            section_comp.participant_count = participant_count
            section_comp.save()
        
        # ترتيب الشعب
        section_competitions = competition.section_battles.order_by(
            '-total_points', '-average_score'
        )
        
        for index, section_comp in enumerate(section_competitions, 1):
            section_comp.previous_rank = section_comp.rank
            section_comp.rank = index
            section_comp.save()
    
    @staticmethod
    def auto_update_competition(competition):
        """تحديث تلقائي للمسابقة"""
        if not competition.auto_ranking:
            return
        
        # تحديث نقاط جميع المشاركين
        for participant in competition.participants.all():
            CompetitionCalculator.calculate_participant_score(participant)
        
        # تحديث الترتيبات
        CompetitionCalculator.update_rankings(competition)
        CompetitionCalculator.update_section_rankings(competition)

class CompetitionRewardManager:
    """مدير جوائز المسابقات"""
    
    @staticmethod
    def award_competition_prizes(competition):
        """منح جوائز المسابقة"""
        if competition.status != Competition.Status.FINISHED:
            return
        
        top_participants = competition.participants.order_by('-total_score')[:10]
        prize_structure = competition.prize_structure
        
        for index, participant in enumerate(top_participants, 1):
            rank_str = str(index)
            if rank_str in prize_structure:
                points = prize_structure[rank_str]
                
                # إنشاء جائزة
                CompetitionReward.objects.create(
                    competition=competition,
                    participant=participant,
                    reward_type=CompetitionReward.RewardType.POINTS,
                    title=f"المركز {index}",
                    description=f"جائزة المركز {index} في {competition.title}",
                    points_value=points
                )
                
                # إضافة النقاط للمشارك
                participant.bonus_score += points
                participant.save()

class CompetitionAnalytics:
    """تحليلات المسابقات"""
    
    @staticmethod
    def get_competition_stats():
        """إحصائيات عامة للمسابقات"""
        now = timezone.now()
        
        total_competitions = Competition.objects.count()
        active_competitions = Competition.objects.filter(
            start_date__lte=now,
            end_date__gte=now,
            status=Competition.Status.ACTIVE
        ).count()
        
        finished_competitions = Competition.objects.filter(
            status=Competition.Status.FINISHED
        ).count()
        
        total_participants = CompetitionParticipant.objects.count()
        
        avg_participants = CompetitionParticipant.objects.values(
            'competition'
        ).annotate(
            count=Count('id')
        ).aggregate(
            avg=Avg('count')
        )['avg'] or 0
        
        # أكثر المسابقات شعبية
        most_popular = Competition.objects.annotate(
            participant_count=Count('participants')
        ).order_by('-participant_count').first()
        
        # أفضل المؤدين
        top_performers = CompetitionParticipant.objects.order_by(
            '-total_score'
        )[:5]
        
        return {
            'total_competitions': total_competitions,
            'active_competitions': active_competitions,
            'finished_competitions': finished_competitions,
            'total_participants': total_participants,
            'average_participants_per_competition': round(avg_participants, 2),
            'most_popular_competition': most_popular,
            'top_performers': top_performers
        }