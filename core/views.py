from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg, Max, Q
from .metricas import ultimos_reportes
from .models import StudentReport, LevelProgressReport
from .permissions import HasValidApiKey
from .serializers import StudentReportSerializer


def dashboard_callback(request, context):
    """Lo que Unfold inyecta en el tablero.

    Marca el primer paso de la visita aqui mismo: el paso es "mira las cifras
    del programa" y esta es esa pantalla, asi que se da por hecho por estar
    delante y no por pulsar nada. Pedir una confirmacion para algo que ya
    acaba de ocurrir es papeleo.
    """
    from .visita import PASO_TABLERO, estado, se_puede_reabrir, marcar

    marcar(request.user, PASO_TABLERO)
    context.update({
        'async_dashboard': True,
        'visita': estado(request.user),
        # Solo si la escondio teniendo tareas pendientes: reabrir una lista
        # entera de tachados no ensena nada.
        'visita_oculta': se_puede_reabrir(request.user),
    })
    return context


# ── API VIEWS ──────────────────────────────────────────────────

class SyncReportView(APIView):
    # La consume la app Android, que no tiene sesion de Django.
    permission_classes = [HasValidApiKey]

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
    permission_classes = [HasValidApiKey]

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
    """Las cifras del tablero.

    **Un reporte es una foto, no un suceso.** Cada sincronización de la app
    manda el estado completo del estudiante —sus preguntas acumuladas, su
    racha, su progreso en cada nivel—, así que la misma práctica aparece
    repetida en todas las fotos posteriores. Agregar sobre todos los reportes
    cuenta la misma pregunta tantas veces como veces haya sincronizado quien
    la respondió.

    Por eso casi todo se calcula sobre **el último reporte de cada estudiante**,
    que es la única fila que describe su estado actual. Es lo que ya hacía la
    lista de estudiantes; aquí no se hacía, y el 12/10/2026 el tablero decía
    2 015 preguntas cuando la cifra real eran 93, veintiún veces más, por sumar
    61 fotos de cuatro estudiantes. El texto de ayuda de la tarjeta de racha ya
    decía «en el último evento de cada usuario»: la documentación estaba bien y
    el código no la seguía.

    Las dos excepciones son deliberadas y están señaladas abajo: el número de
    sincronizaciones y el mapa de calor sí cuentan reportes, porque lo que
    miden es precisamente la actividad de sincronización.
    """

    def get(self, request):
        from django.db.models.functions import TruncDate

        ultimos = ultimos_reportes()

        # Estadísticas generales
        total_students = StudentReport.objects.values('username').distinct().count()
        # Esta sí cuenta todos los reportes: la tarjeta se llama
        # «Sincronizaciones» y eso es justo lo que mide.
        total_reports = StudentReport.objects.count()
        total_questions = ultimos.aggregate(
            total=Sum('total_questions_answered')
        )['total'] or 0
        avg_streak = ultimos.aggregate(
            avg=Avg('current_streak_days')
        )['avg'] or 0

        # Progreso por competencia, solo sobre la última foto de cada
        # estudiante: en todas las anteriores vuelven a aparecer los mismos
        # niveles, así que contarlas todas multiplicaba los dos números por el
        # número de sincronizaciones.
        competence_progress = list(
            LevelProgressReport.objects
            .filter(report__in=ultimos)
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

        # Comparativa de cohortes, también sobre la última foto de cada uno.
        # Agrupada por el programa del catalogo y no por el texto que escribio
        # cada uno: si no, la misma carrera escrita de dos formas aparecia
        # como dos cohortes, cada una con la mitad de la gente.
        cohorts = list(
            ultimos
            .values('variante_programa__programa__nombre')
            .annotate(
                avg_questions=Avg('total_questions_answered'),
                avg_streak=Avg('current_streak_days'),
                students=Count('username', distinct=True)
            )
            .exclude(variante_programa__programa__isnull=True)
            .order_by('-students')
        )
        # La plantilla espera la clave de siempre.
        for c in cohorts:
            c['academic_program'] = c.pop('variante_programa__programa__nombre')

        # Últimos reportes
        latest_reports = list(StudentReport.objects.order_by('-reported_at')[:5].values(
            'username', 'total_questions_answered', 'current_streak_days', 'reported_at'
        ))

        return Response({
            # Un panel recien purgado no es un panel roto, pero lo parece:
            # cuatro ceros y un mapa de calor en blanco. Esta bandera deja que
            # la pagina lo diga con palabras en vez de dejarlo a la
            # interpretacion de quien mira.
            'panel_vacio': total_students == 0,
            'total_students': total_students,
            'total_reports': total_reports,
            'total_questions': total_questions,
            'avg_streak': round(avg_streak, 1),
            'competence_progress': competence_progress,
            'heatmap_data': heatmap_data,
            'cohorts': cohorts,
            'latest_reports': latest_reports,
        })
