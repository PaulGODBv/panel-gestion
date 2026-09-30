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
