from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg, Max, Q
from .models import StudentReport, LevelProgressReport
from .serializers import StudentReportSerializer


def dashboard_callback(request, context):
    # Estadísticas generales
    total_students = StudentReport.objects.values('username').distinct().count()
    total_reports = StudentReport.objects.count()
    total_questions = StudentReport.objects.aggregate(
        total=Sum('total_questions_answered')
    )['total'] or 0
    avg_streak = StudentReport.objects.aggregate(
        avg=Avg('current_streak_days')
    )['avg'] or 0

    # Progreso por competencia
    competence_progress = (
        LevelProgressReport.objects
        .values('competence_name')
        .annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(is_completed=True))
        )
        .order_by('competence_name')
    )

    # Últimos 5 reportes
    latest_reports = StudentReport.objects.order_by('-reported_at')[:5]

    context.update({
        'total_students': total_students,
        'total_reports': total_reports,
        'total_questions': total_questions,
        'avg_streak': round(avg_streak, 1),
        'competence_progress': list(competence_progress),
        'latest_reports': latest_reports,
    })

    return context


# ── API VIEWS ──────────────────────────────────────────────────

class SyncReportView(APIView):
    def post(self, request):
        serializer = StudentReportSerializer(data=request.data)
        if serializer.is_valid():
            report = serializer.save()
            return Response(
                {
                    'success': True,
                    'message': f'Reporte de {report.username} guardado correctamente',
                    'report_id': report.id
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentListView(APIView):
    def get(self, request):
        latest_ids = (
            StudentReport.objects
            .values('username')
            .annotate(latest=Max('id'))
            .values_list('latest', flat=True)
        )
        reports = StudentReport.objects.filter(
            id__in=latest_ids
        ).order_by('username')
        serializer = StudentReportSerializer(reports, many=True)
        return Response(serializer.data)


class StudentDetailView(APIView):
    def get(self, request, username):
        reports = StudentReport.objects.filter(
            username=username
        ).prefetch_related('level_progress').order_by('-reported_at')

        if not reports.exists():
            return Response(
                {'error': f'No se encontraron reportes para {username}'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = StudentReportSerializer(reports, many=True)
        return Response({
            'username': username,
            'total_reports': reports.count(),
            'reports': serializer.data
        })
