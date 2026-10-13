from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Max, Sum, Avg, Count, Q
from .models import StudentReport, LevelProgressReport


@method_decorator(staff_member_required, name='dispatch')
class StudentListAdminView(TemplateView):
    template_name = 'admin/students/list.html'

    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'csv':
            return self.export_csv(request)
        return super().get(request, *args, **kwargs)

    def export_csv(self, request):
        import csv
        from django.http import HttpResponse
        
        students = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="estudiantes.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Usuario', 'Email', 'Programa', 'Reporte Mas Reciente', 'Preguntas Totales', 'Racha Actual', 'Estado'])
        
        for student in students:
            writer.writerow([
                student.username,
                student.email,
                student.academic_program or 'N/A',
                student.reported_at.strftime('%Y-%m-%d %H:%M:%S'),
                student.total_questions_answered,
                student.current_streak_days,
                student.risk_status
            ])
            
        return response

    def get_queryset(self):
        search = self.request.GET.get('q', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')

        latest_ids = (
            StudentReport.objects
            .values('username')
            .annotate(latest=Max('id'))
            .values_list('latest', flat=True)
        )

        students = StudentReport.objects.filter(id__in=latest_ids)

        if search:
            students = students.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )
            
        if date_from:
            students = students.filter(reported_at__date__gte=date_from)
        if date_to:
            students = students.filter(reported_at__date__lte=date_to)

        return students.order_by('username')

    def get_context_data(self, **kwargs):
        # Obtener contexto base de Admin (necesario para Unfold)
        context = admin.site.each_context(self.request)
        context.update(super().get_context_data(**kwargs))

        students = self.get_queryset()

        context.update({
            'title': 'Estudiantes',
            'students': students,
            'search': self.request.GET.get('q', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'total_count': students.count(),
        })
        return context


@method_decorator(staff_member_required, name='dispatch')
class StudentDetailAdminView(TemplateView):
    template_name = 'admin/students/detail.html'

    def get_context_data(self, **kwargs):
        from .visita import PASO_ESTUDIANTE, marcar

        marcar(self.request.user, PASO_ESTUDIANTE)

        # Obtener contexto base de Admin (necesario para Unfold)
        context = admin.site.each_context(self.request)
        context.update(super().get_context_data(**kwargs))

        username = self.kwargs['username']

        reports = StudentReport.objects.filter(
            username=username
        ).prefetch_related('level_progress').order_by('reported_at')

        if not reports.exists():
            context['error'] = f'No se encontraron reportes para {username}'
            return context

        latest = reports.last()

        competence_progress = (
            LevelProgressReport.objects
            .filter(report__username=username)
            .values('competence_name')
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(is_completed=True)),
                avg_score=Avg('score'),
                total_time=Sum('time_spent_seconds')
            )
            .order_by('competence_name')
        )

        evolution = reports.values(
            'reported_at',
            'total_questions_answered',
            'current_streak_days',
            'daily_practice_time_seconds'
        )

        completed_levels = (
            LevelProgressReport.objects
            .filter(report__username=username, is_completed=True)
            .values('competence_name', 'level_name')
            .distinct()
            .order_by('competence_name', 'level_name')
        )

        # Las seis insignias de la app, con sus mismos umbrales. Se decide aquí
        # y no en la plantilla porque {% include with %} no admite
        # comparaciones, y repetir seis bloques {% if %} invita a que un umbral
        # se quede desfasado respecto a la app.
        #
        # Las de racha se miden contra max_streak_days, no contra la racha
        # viva: un logro conseguido no se devuelve, igual que en el teléfono.
        preguntas = latest.total_questions_answered
        mejor_racha = latest.max_streak_days
        logros = [
            {'icon': 'gps_fixed', 'title': 'Primer Intento',
             'req': 'Responde tu primera pregunta', 'unlocked': preguntas >= 1},
            {'icon': 'local_fire_department', 'title': 'Constancia',
             'req': 'Racha de 3 días', 'unlocked': mejor_racha >= 3},
            {'icon': 'bolt', 'title': 'Semana Completa',
             'req': 'Racha de 7 días', 'unlocked': mejor_racha >= 7},
            {'icon': 'military_tech', 'title': 'Imparable',
             'req': 'Racha de 15 días', 'unlocked': mejor_racha >= 15},
            {'icon': 'workspace_premium', 'title': 'Maestro Básico',
             'req': 'Responde 50 preguntas', 'unlocked': preguntas >= 50},
            {'icon': 'rocket', 'title': 'Explorador',
             'req': 'Responde 100 preguntas', 'unlocked': preguntas >= 100},
        ]

        context.update({
            'title': f'Estudiante: {username}',
            'username': username,
            'latest': latest,
            'logros': logros,
            'total_reports': reports.count(),
            'reports': reports,
            'competence_progress': list(competence_progress),
            'evolution': list(evolution),
            'completed_levels': list(completed_levels),
        })
        return context


@method_decorator(staff_member_required, name='dispatch')
class ExplorerAdminView(TemplateView):
    """Explorador de metricas: cruzar programa, competencia, nivel y fechas.

    Es TODO-6. El tablero contesta «como va todo»; esto contesta «como va
    esto», que es la pregunta que de verdad hace Desarrollo Estudiantil.

    **Sin libreria de graficos.** Las barras se dibujan con `rt-progress`, que
    ya existe en la hoja de estilos del panel. Anadir Chart.js habria traido
    una dependencia por CDN, un segundo lenguaje visual que no es el del resto
    del panel, y una pagina que no ensena nada con JavaScript desactivado ni
    en una captura de pantalla para la memoria.

    **Todo se calcula en el servidor y se filtra por GET.** Asi una consulta
    concreta —Enfermeria en Lectura Critica el ultimo mes— es una direccion
    que se puede guardar o pegar en un correo, que es como se comparte un
    hallazgo de verdad.
    """
    template_name = 'admin/explorador.html'

    def get_context_data(self, **kwargs):
        from .metricas import (
            cobertura, mejor_y_peor, por_competencia, por_programa,
            progreso_filtrado, ultimos_reportes,
        )

        # Contexto base del admin, que Unfold necesita: de ahi salen la barra
        # lateral y la hoja de estilos propia del panel, que se inyecta por
        # UNFOLD["STYLES"]. Sin esta linea la pagina se dibuja entera pero sin
        # una sola regla de estilo, que es exactamente como salio la primera vez.
        from .visita import PASO_EXPLORADOR, marcar

        marcar(self.request.user, PASO_EXPLORADOR)

        ctx = admin.site.each_context(self.request)
        ctx.update(super().get_context_data(**kwargs))
        ctx['title'] = 'Explorador'
        g = self.request.GET

        programa = g.get('programa', '').strip()
        competencia = g.get('competencia', '').strip()
        nivel = g.get('nivel', '').strip()
        desde = g.get('desde', '').strip() or None
        hasta = g.get('hasta', '').strip() or None

        filas = progreso_filtrado(
            programa=programa, competencia=competencia, nivel=nivel,
            desde=desde, hasta=hasta,
        )
        competencias = por_competencia(filas)
        mejor, peor = mejor_y_peor(competencias)

        # Las listas de los desplegables salen de lo que hay, no de un catalogo
        # fijo: un filtro que ofrece opciones sin un solo dato detras solo sirve
        # para llevar a una pantalla vacia.
        todas = LevelProgressReport.objects.filter(report__in=ultimos_reportes())

        # El orden de las columnas se fija una vez y lo comparten la cabecera de
        # la tabla y las celdas de cada fila. Si se calcularan por separado,
        # bastaria una competencia sin datos para desplazar toda una fila y que
        # los numeros quedaran bajo la columna equivocada.
        columnas = sorted(c['nombre'] for c in competencias if c['preguntas'])

        ctx.update({
            'competencias': competencias,
            'mejor': mejor,
            'peor': peor,
            'programas': por_programa(filas, columnas),
            'cobertura': cobertura(filas),
            'nombres_de_competencia': columnas,
            'filtros': {
                'programa': programa, 'competencia': competencia,
                'nivel': nivel, 'desde': desde or '', 'hasta': hasta or '',
            },
            'hay_filtros': any([programa, competencia, nivel, desde, hasta]),
            'opciones_programa': sorted(
                p for p in ultimos_reportes()
                .values_list('academic_program', flat=True).distinct() if p
            ),
            'opciones_competencia': list(
                todas.values('competence_id', 'competence_name')
                .distinct().order_by('competence_name')
            ),
            'opciones_nivel': list(
                todas.values('level_id', 'level_name', 'competence_name')
                .distinct().order_by('competence_name', 'level_name')
            ),
        })
        return ctx


@method_decorator(staff_member_required, name='dispatch')
class VisitaGuiadaView(TemplateView):
    """Cerrar la tarjeta de primeros pasos, o volver a abrirla.

    Solo por POST: cambia algo del lado del servidor, y un enlace que cambia
    estado se dispara solo con cualquier cosa que precargue las direcciones de
    la pagina.

    Cerrar no es irreversible a proposito. El enlace para volver a abrirla
    queda en el pie del tablero, porque esconder algo sin dejar forma de
    recuperarlo convierte un descarte en una perdida.
    """

    def post(self, request, *args, **kwargs):
        from django.shortcuts import redirect

        from .visita import _registro

        registro = _registro(request.user)
        registro.cerrada = request.POST.get('accion') != 'abrir'
        registro.save(update_fields=['cerrada', 'actualizada_en'])
        return redirect('admin:index')
