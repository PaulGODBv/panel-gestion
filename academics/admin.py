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
        'formato_practica',
        'is_Locked_by_default',
        'question_count',
        'coverage_indicator'
    ]
    list_filter = ['competence', 'formato_practica']
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

    list_display = ['vista_previa', 'alt_text', 'es_figura', 'uso', 'updated_at']
    list_filter = ['es_figura']
    search_fields = ['alt_text', 'caption']
    readonly_fields = ['vista_previa_grande', 'created_at', 'updated_at']
    fields = ['image', 'vista_previa_grande', 'es_figura', 'alt_text', 'caption',
              'created_at', 'updated_at']

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
            path('importar/', self.admin_site.admin_view(self.importar_pegando), name='academics_question_importar'),
        ]
        return custom_urls + urls
        
    def importar_pegando(self, request):
        """Pegar preguntas escritas a mano, revisarlas y solo entonces guardar.

        Tres diferencias con el importador de CSV, y las tres vienen del mismo
        sitio: quien sube las preguntas no es quien programo el panel.

        1. **El nivel se elige de una lista**, no se escribe su id. Nadie fuera
           del equipo sabe que «18» es Comunicacion Escrita.
        2. **Se ve antes de escribir.** El CSV guardaba fila a fila segun
           leia: si la quinta estaba mal, las cuatro primeras ya estaban
           dentro y habia que ir a borrarlas a mano.
        3. **Entra todo o no entra nada.** La escritura va en una transaccion.

        El texto no se guarda entre la revision y la confirmacion: se vuelve a
        mandar y se vuelve a analizar. Es deliberado — guardarlo en sesion
        abriria la puerta a confirmar algo distinto de lo que se enseno, que
        es justo la confianza que esta pantalla tiene que ganarse.
        """
        import hashlib

        from django.contrib import messages
        from django.db import transaction
        from django.shortcuts import redirect, render

        from .importador import analizar, normalizar, resumen

        niveles = Level.objects.select_related("competence").order_by(
            "competence__order", "order", "id"
        )

        texto = request.POST.get("texto", "")
        id_de_nivel = request.POST.get("nivel", "")
        accion = request.POST.get("accion", "")

        bloques = []
        nivel = None
        if request.method == "POST":
            nivel = niveles.filter(pk=id_de_nivel).first()
            if nivel is None:
                messages.error(request, "Elige el nivel al que van estas preguntas.")
            elif not texto.strip():
                messages.error(request, "No hay nada que leer: el cuadro está vacío.")
            else:
                bloques = analizar(texto)
                self._marcar_duplicadas(bloques, nivel, normalizar)

        # Huella del texto que se reviso. Al confirmar se vuelve a calcular: si
        # alguien edito el cuadro despues de revisar, no se guarda lo que no se
        # ha ensenado, se vuelve a revisar. Es la unica forma de que "entra lo
        # que viste" sea verdad teniendo el texto a la vista todo el rato.
        huella = hashlib.sha256(texto.encode("utf-8")).hexdigest()
        if accion == "confirmar" and huella != request.POST.get("huella", ""):
            messages.warning(
                request,
                "El texto cambió después de revisarlo, así que no se guardó nada. "
                "Aquí tienes la revisión de lo que hay ahora.",
            )
            accion = "revisar"

        if accion == "confirmar" and nivel is not None and bloques:
            creadas = []
            with transaction.atomic():
                for bloque in bloques:
                    if not bloque.valida:
                        continue
                    pregunta = Question.objects.create(
                        level=nivel,
                        text=bloque.enunciado,
                        reading_text=bloque.contexto,
                        explanation=bloque.explicacion,
                        correct_option_order=bloque.orden_de_la_correcta,
                    )
                    for orden, opcion in enumerate(bloque.opciones, start=1):
                        QuestionOption.objects.create(
                            question=pregunta, text=opcion.texto, order=orden
                        )
                    creadas.append(pregunta)

            if creadas:
                # El paso se da por hecho al guardar, no al abrir la pantalla:
                # lo que la lista promete es "carga preguntas", no "asomate".
                from core.visita import PASO_CARGA, marcar
                marcar(request.user, PASO_CARGA)

                messages.success(
                    request,
                    f"{len(creadas)} pregunta(s) creada(s) en «{nivel.name}». "
                    "Las que necesiten imagen se la pones desde su ficha.",
                )
            else:
                messages.warning(request, "No había ninguna pregunta lista para guardar.")
            return redirect("admin:academics_question_changelist")

        return render(
            request,
            "admin/academics/question/importar_pegando.html",
            context=dict(
                self.admin_site.each_context(request),
                niveles=niveles,
                nivel=nivel,
                texto=texto,
                bloques=bloques,
                resumen=resumen(bloques) if bloques else None,
                revisado=bool(bloques),
                huella=huella if request.method == "POST" else "",
            ),
        )

    @staticmethod
    def _marcar_duplicadas(bloques, nivel, normalizar):
        """Senala las que ya estan en ESE nivel, no en el banco entero.

        La misma pregunta en dos niveles distintos es legitima y deliberada:
        las versiones cortas de Calentamiento conviven con sus originales en
        los niveles de evaluacion. Lo que no tiene sentido es repetirla dentro
        del mismo nivel, que es lo que pasa al subir dos veces el mismo lote.
        """
        existentes = {
            normalizar(t): pk
            for pk, t in Question.objects.filter(level=nivel).values_list("id", "text")
        }
        vistas = {}
        for bloque in bloques:
            clave = normalizar(bloque.enunciado)
            if not clave:
                continue
            if clave in existentes:
                bloque.duplicada_de = existentes[clave]
            elif clave in vistas:
                bloque.duplicada_de = 0  # repetida dentro del propio texto pegado
                bloque.avisos.append(
                    f"Esta pregunta ya aparece más arriba, en el bloque {vistas[clave]}."
                )
            else:
                vistas[clave] = bloque.numero

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
