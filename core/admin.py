from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import StudentReport, LevelProgressReport


@admin.register(StudentReport)
class StudentReportAdmin(ModelAdmin):
    list_display = [
        'username',
        'email',
        'total_questions_answered',
        'current_streak_days',
        'practice_time_formatted',
        'reported_at'
    ]
    list_filter = ['reported_at']
    search_fields = ['username', 'email']
    readonly_fields = ['reported_at', 'practice_time_formatted']
    ordering = ['-reported_at']


@admin.register(LevelProgressReport)
class LevelProgressReportAdmin(ModelAdmin):
    list_display = [
        'report',
        'competence_name',
        'level_name',
        'score',
        'total_questions',
        'percentage',
        'is_completed'
    ]
    list_filter = ['competence_name', 'is_completed']
    search_fields = ['report__username', 'competence_name', 'level_name']
    readonly_fields = ['percentage']
