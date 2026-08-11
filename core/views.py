from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import StudentReport
from .serializers import StudentReportSerializer


class SyncReportView(APIView):
    """
    POST /api/reports/sync/
    Android envía el reporte de progreso del estudiante
    """
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
            {
                'success': False,
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentListView(APIView):
    """
    GET /api/reports/students/
    Lista todos los estudiantes con sus últimos reportes
    """
    def get(self, request):
        # Agrupar por username, tomar el último reporte de cada uno
        from django.db.models import Max
        latest_ids = (
            StudentReport.objects
            .values('username')
            .annotate(latest=Max('id'))
            .values_list('latest', flat=True)
        )
        reports = StudentReport.objects.filter(id__in=latest_ids).order_by('username')
        serializer = StudentReportSerializer(reports, many=True)
        return Response(serializer.data)


class StudentDetailView(APIView):
    """
    GET /api/reports/students/<username>/
    Historial completo de un estudiante
    """
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
