from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import StudentReport, LevelProgressReport


@admin.register(StudentReport)
class StudentReportAdmin(ModelAdmin):
    list_display = [
        'username',
        'academic_program',
        'total_questions_answered',
        'current_streak_days',
        'practice_time_formatted',
        'risk_status_tag',
        'reported_at'
    ]
    list_filter = ['reported_at', 'academic_program']
    search_fields = ['username', 'email', 'academic_program']
    readonly_fields = ['reported_at', 'practice_time_formatted', 'risk_status_tag']
    ordering = ['-reported_at']

    def risk_status_tag(self, obj):
        from django.utils.html import format_html
        status = obj.risk_status
        if status == 'activo':
            color = 'bg-green-100 text-green-700 border-green-200'
            label = 'Activo'
        elif status == 'en_riesgo':
            color = 'bg-red-100 text-red-700 border-red-200'
            label = 'En Riesgo'
        else:
            color = 'bg-gray-100 text-gray-700 border-gray-200'
            label = 'Inactivo'

        return format_html(
            '<span class="px-2 py-1 rounded-full text-xs font-medium border {}">{}</span>',
            color, label
        )
    risk_status_tag.short_description = 'Estado'


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
