from django.contrib import admin
from .models import (
    Competition, CompetitionParticipant, SectionCompetition,
    CompetitionRound, CompetitionVote, CompetitionReward
)

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ['title', 'competition_type', 'status', 'start_date', 'end_date', 'participant_count']
    list_filter = ['competition_type', 'status', 'period', 'is_featured']
    search_fields = ['title', 'description']
    filter_horizontal = ['sections']
    readonly_fields = ['participant_count']
    
    fieldsets = (
        ('معلومات أساسية', {
            'fields': ('title', 'description', 'competition_type', 'period', 'status')
        }),
        ('التوقيت', {
            'fields': ('start_date', 'end_date')
        }),
        ('إعدادات المشاركة', {
            'fields': ('sections', 'max_participants')
        }),
        ('نظام النقاط', {
            'fields': ('early_submission_points', 'on_time_points', 'late_penalty', 'prize_structure')
        }),
        ('إعدادات متقدمة', {
            'fields': ('auto_ranking', 'allow_voting', 'is_featured')
        })
    )

@admin.register(CompetitionParticipant)
class CompetitionParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'competition', 'total_score', 'rank', 'joined_at']
    list_filter = ['competition', 'joined_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'competition__title']
    readonly_fields = ['total_score', 'joined_at', 'last_activity']

@admin.register(SectionCompetition)
class SectionCompetitionAdmin(admin.ModelAdmin):
    list_display = ['section', 'competition', 'total_points', 'rank', 'participant_count']
    list_filter = ['competition']
    readonly_fields = ['total_points', 'average_score', 'participant_count']

@admin.register(CompetitionRound)
class CompetitionRoundAdmin(admin.ModelAdmin):
    list_display = ['competition', 'round_number', 'title', 'start_date', 'end_date']
    list_filter = ['competition']
    ordering = ['competition', 'round_number']

@admin.register(CompetitionVote)
class CompetitionVoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'candidate', 'competition', 'vote_weight', 'created_at']
    list_filter = ['competition', 'vote_weight', 'created_at']
    search_fields = ['voter__username', 'candidate__username']

@admin.register(CompetitionReward)
class CompetitionRewardAdmin(admin.ModelAdmin):
    list_display = ['participant', 'competition', 'reward_type', 'title', 'points_value', 'awarded_at']
    list_filter = ['reward_type', 'competition', 'awarded_at']
    search_fields = ['participant__user__username', 'title']