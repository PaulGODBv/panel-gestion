from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Competence, Level, Question, QuestionOption


class LevelInline(TabularInline):
    model = Level
    extra = 1
    fields = ['name', 'description', 'order', 'is_Locked_by_default']


class QuestionOptionInline(TabularInline):
    model = QuestionOption
    extra = 4
    fields = ['text', 'order']


@admin.register(Competence)
class CompetenceAdmin(ModelAdmin):
    list_display = ['name', 'order', 'level_count']
    ordering = ['order']
    inlines = [LevelInline]

    def level_count(self, obj):
        return obj.levels.count()
    level_count.short_description = 'Niveles'


@admin.register(Level)
class LevelAdmin(ModelAdmin):
    list_display = [
        'name',
        'competence',
        'order',
        'is_Locked_by_default',
        'question_count'
    ]
    list_filter = ['competence']
    ordering = ['competence', 'order']

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Preguntas'


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = [
        'short_text',
        'level',
        'correct_option_order',
        'created_at'
    ]
    list_filter = ['level__competence', 'level']
    search_fields = ['text']
    ordering = ['level', 'created_at']
    inlines = [QuestionOptionInline]

    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    short_text.short_description = 'Enunciado'
