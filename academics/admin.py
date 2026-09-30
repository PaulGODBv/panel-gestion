from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from simple_history.admin import SimpleHistoryAdmin
from .models import Competence, ContextAsset, Level, Question, QuestionOption
from django.utils.html import format_html


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
        'question_count',
        'coverage_indicator'
    ]
    list_filter = ['competence']
    ordering = ['competence', 'order']

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Preguntas'

    def coverage_indicator(self, obj):
        count = obj.questions.count()
        if count < 10:
            color = 'bg-red-500'
            label = 'Bajo'
        elif count <= 20:
            color = 'bg-yellow-500'
            label = 'Medio'
        else:
            color = 'bg-green-500'
            label = 'Óptimo'
        return format_html(
            '<div class="flex items-center gap-2">'
            '<span class="w-3 h-3 rounded-full {}"></span>'
            '<span class="text-xs">{} ({})</span>'
            '</div>',
            color, label, count
        )
    coverage_indicator.short_description = 'Cobertura'


@admin.register(ContextAsset)
class ContextAssetAdmin(ModelAdmin):
    """Banco de imagenes de contexto.

    Aqui es donde se sube el archivo. Antes la pregunta pedia el *nombre* de un
    drawable que tenia que estar ya compilado dentro del APK, asi que el campo
    era de texto y solo servia si alguien habia metido la imagen en el proyecto
    Android: el encargado de contenidos no podia anadir una imagen nueva.
    """

    list_display = ['vista_previa', 'alt_text', 'uso', 'updated_at']
    search_fields = ['alt_text', 'caption']
    readonly_fields = ['vista_previa_grande', 'created_at', 'updated_at']
    fields = ['image', 'vista_previa_grande', 'alt_text', 'caption', 'created_at', 'updated_at']

    @admin.display(description="Imagen")
    def vista_previa(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" style="height:48px;border-radius:4px;" alt="{}">',
            obj.image.url, obj.alt_text,
        )

    @admin.display(description="Vista previa")
    def vista_previa_grande(self, obj):
        if not obj.image:
            return "Sube una imagen para verla aqui."
        return format_html(
            '<img src="{}" style="max-width:520px;width:100%;border-radius:8px;" alt="{}">',
            obj.image.url, obj.alt_text,
        )

    @admin.display(description="Preguntas que la usan")
    def uso(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = [
        'short_text',
        'level',
        'correct_option_order',
        'created_at'
    ]
    list_filter = ['level__competence', 'level', 'is_active']
    search_fields = ['text']
    ordering = ['level', 'created_at']
    inlines = [QuestionOptionInline]
    autocomplete_fields = ['context_asset']
    readonly_fields = ['imagen_actual', 'created_at', 'updated_at']
    fieldsets = [
        (None, {'fields': ['level', 'text', 'reading_text', 'correct_option_order', 'explanation']}),
        ('Imagen de contexto', {
            'fields': ['context_asset', 'imagen_actual'],
            'description': 'La imagen se sube en «Imagenes de contexto» y se '
                           'reutiliza entre preguntas. El campo de texto antiguo '
                           'se conserva solo para las versiones de la app que '
                           'todavia resuelven el nombre contra el APK.',
        }),
        ('Publicacion', {'fields': ['is_active', 'context_image', 'created_at', 'updated_at']}),
    ]
    
    @admin.display(description="Vista previa")
    def imagen_actual(self, obj):
        if not (obj.context_asset and obj.context_asset.image):
            return "Sin imagen."
        return format_html(
            '<img src="{}" style="max-width:420px;width:100%;border-radius:8px;" alt="{}">',
            obj.context_asset.image.url, obj.context_asset.alt_text,
        )

    change_form_template = 'admin/academics/question/change_form.html'
    change_list_template = 'admin/academics/question/change_list.html'
    
    class Media:
        css = {
            'all': ('academics/css/question_admin.css',)
        }
        js = ('academics/js/question_admin.js',)

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='academics_question_import_csv'),
        ]
        return custom_urls + urls
        
    def import_csv(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        import csv
        import io
        
        if request.method == "POST":
            csv_file = request.FILES.get("csv_file")
            if not csv_file or not csv_file.name.endswith('.csv'):
                messages.error(request, 'Por favor sube un archivo CSV válido.')
                return redirect('..')
                
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string) # skip header
            
            # Formato esperado: nivel_id, enunciado, texto_lectura, opcion_correcta (1-4), opc1, opc2, opc3, opc4
            for row in csv.reader(io_string, delimiter=',', quotechar='"'):
                try:
                    level_id = int(row[0])
                    text = row[1]
                    reading = row[2]
                    correct = int(row[3])
                    options = row[4:8]
                    
                    level = Level.objects.get(id=level_id)
                    q = Question.objects.create(
                        level=level,
                        text=text,
                        reading_text=reading,
                        correct_option_order=correct
                    )
                    
                    for i, opt_text in enumerate(options, start=1):
                        if opt_text:
                            QuestionOption.objects.create(question=q, text=opt_text, order=i)
                except Exception as e:
                    messages.error(request, f'Error en fila: {row} - {str(e)}')
                    
            messages.success(request, 'Importación completada.')
            return redirect('..')
            
        return render(request, "admin/academics/question/import_csv.html", context=dict(
           self.admin_site.each_context(request),
        ))

    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    short_text.short_description = 'Enunciado'
