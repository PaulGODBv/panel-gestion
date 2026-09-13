from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg, Max, Q
from .models import StudentReport, LevelProgressReport
from .serializers import StudentReportSerializer


def dashboard_callback(request, context):
    context.update({
        'async_dashboard': True,
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


class RankingView(APIView):
    def get(self, request):
        username = request.query_params.get('username', '')

        # Top 10 por preguntas respondidas (último reporte por usuario)
        latest_ids = (
            StudentReport.objects
            .values('username')
            .annotate(latest=Max('id'))
            .values_list('latest', flat=True)
        )

        ranking = (
            StudentReport.objects
            .filter(id__in=latest_ids)
            .order_by('-total_questions_answered')
            .values('username', 'total_questions_answered')
        )

        # Construir top 10 con posición
        top10 = []
        user_position = None
        user_score = None

        for index, entry in enumerate(ranking, start=1):
            if index <= 10:
                top10.append({
                    'position': index,
                    'username': entry['username'],
                    'total_questions_answered': entry['total_questions_answered'],
                    'is_current_user': entry['username'] == username
                })
            if entry['username'] == username:
                user_position = index
                user_score = entry['total_questions_answered']

        return Response({
            'top10': top10,
            'current_user': {
                'username': username,
                'position': user_position,
                'total_questions_answered': user_score,
                'in_top10': user_position is not None and user_position <= 10
            } if username else None
        })


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

class DashboardDataAPIView(APIView):
    def get(self, request):
        from django.db.models.functions import TruncDate
        
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
        competence_progress = list(
            LevelProgressReport.objects
            .values('competence_name')
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(is_completed=True))
            )
            .order_by('competence_name')
        )

        # Heatmap data (práctica diaria)
        heatmap_query = (
            StudentReport.objects
            .annotate(date=TruncDate('reported_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        # Format for cal-heatmap or similar: {timestamp: count}
        import time
        heatmap_data = {
            int(time.mktime(item['date'].timetuple())): item['count']
            for item in heatmap_query if item['date']
        }

        # Comparativa de cohortes
        cohorts = list(
            StudentReport.objects
            .values('academic_program')
            .annotate(
                avg_questions=Avg('total_questions_answered'),
                avg_streak=Avg('current_streak_days'),
                students=Count('username', distinct=True)
            )
            .exclude(academic_program__isnull=True)
            .exclude(academic_program='')
            .order_by('-students')
        )

        # Últimos reportes
        latest_reports = list(StudentReport.objects.order_by('-reported_at')[:5].values(
            'username', 'total_questions_answered', 'current_streak_days', 'reported_at'
        ))

        return Response({
            'total_students': total_students,
            'total_reports': total_reports,
            'total_questions': total_questions,
            'avg_streak': round(avg_streak, 1),
            'competence_progress': competence_progress,
            'heatmap_data': heatmap_data,
            'cohorts': cohorts,
            'latest_reports': latest_reports,
        })
