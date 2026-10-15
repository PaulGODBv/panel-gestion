from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    StudentReport,
    LevelProgressReport,
    ProgramaAcademico,
    VarianteDePrograma,
)


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
    list_filter = ['reported_at', 'variante_programa__programa']
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

# Vuelve a registrar User y Group con el admin de Unfold. Sin esto sus
# formularios usan los widgets de serie de Django y los campos salen sin
# borde ni fondo: invisibles hasta pulsarlos.
from . import admin_cuentas  # noqa: F401,E402


@admin.register(ProgramaAcademico)
class ProgramaAcademicoAdmin(ModelAdmin):
    """El catálogo oficial. Se consulta más de lo que se edita."""

    list_display = ['nombre', 'nivel', 'activo', 'cuantas_variantes']
    list_filter = ['nivel', 'activo']
    search_fields = ['nombre']
    ordering = ['nivel', 'nombre']

    def cuantas_variantes(self, obj):
        return obj.variantes.count()
    cuantas_variantes.short_description = 'Variantes'


@admin.register(VarianteDePrograma)
class VarianteDeProgramaAdmin(ModelAdmin):
    """Cada forma en que alguien escribió su programa, y a cuál corresponde.

    Esta pantalla existe para una tarea concreta: asignar las variantes que el
    sistema no puede resolver solo. «Ingeniería de software» se engancha sola
    porque normalizada es idéntica a la del catálogo; «Admon Negocios
    Internacionales» no, y eso lo decide una persona.

    Se asigna desde la propia lista —`list_editable`— porque obligar a entrar
    en cada ficha para cambiar un desplegable convierte diez minutos en media
    hora. El filtro de arriba abre directamente en las que faltan.
    """

    list_display = ['texto_original', 'programa', 'cuantos_reportes']
    list_editable = ['programa']
    list_filter = ['programa']
    search_fields = ['texto_original', 'texto_normalizado']
    readonly_fields = ['texto_normalizado']
    ordering = ['programa', 'texto_normalizado']

    def cuantos_reportes(self, obj):
        return obj.reportes.count()
    cuantos_reportes.short_description = 'Reportes'
