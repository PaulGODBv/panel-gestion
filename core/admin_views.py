from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Max, Sum, Avg, Count, Q
from .models import StudentReport, LevelProgressReport


@method_decorator(staff_member_required, name='dispatch')
class StudentListAdminView(TemplateView):
    template_name = 'admin/students/list.html'

    def get_context_data(self, **kwargs):
        # Obtener contexto base de Admin (necesario para Unfold)
        context = admin.site.each_context(self.request)
        context.update(super().get_context_data(**kwargs))

        search = self.request.GET.get('q', '')

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

        students = students.order_by('username')

        context.update({
            'title': 'Estudiantes',
            'students': students,
            'search': search,
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

        context.update({
            'title': f'Estudiante: {username}',
            'username': username,
            'latest': latest,
            'total_reports': reports.count(),
            'reports': reports,
            'competence_progress': list(competence_progress),
            'evolution': list(evolution),
            'completed_levels': list(completed_levels),
        })
        return context
