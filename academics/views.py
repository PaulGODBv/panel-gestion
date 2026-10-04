from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.permissions import HasValidApiKey
from .models import Competence, Level, Question
from .serializers import (
    CompetenceSerializer,
    LevelSerializer,
    QuestionSerializer
)


class CompetenceListView(APIView):
    """
    GET /api/competences/
    Devuelve todas las competencias con sus niveles (sin preguntas)
    """

    # Endpoint pensado para la app: se protege con la clave compartida, no con
    # sesion de staff. Hoy la app trae el contenido embebido y no lo llama.
    permission_classes = [HasValidApiKey]

    def get(self, request):
        competences = Competence.objects.prefetch_related('levels').all()
        serializer = CompetenceSerializer(competences, many=True)
        return Response(serializer.data)


class QuestionsByLevelView(APIView):
    """
    GET /api/questions/<level_id>/
    Devuelve todas las preguntas de un nivel con sus opciones
    """

    permission_classes = [HasValidApiKey]

    def get(self, request, level_id):
        try:
            level = Level.objects.get(id=level_id)
            # select_related evita una consulta por pregunta para la imagen y
            # el nivel; is_active deja fuera las retiradas sin borrarlas.
            questions = (
                Question.objects
                .filter(level=level, is_active=True)
                .select_related('context_asset', 'level')
                .prefetch_related('options')
            )
            # El contexto con la peticion es lo que permite devolver la URL de
            # la imagen absoluta. Sin el, el telefono recibiria "/media/..." y
            # no sabria contra que host resolverlo.
            serializer = QuestionSerializer(questions, many=True, context={'request': request})
            return Response({
                'level_id': level_id,
                'level_name': level.name,
                # Como se juega este nivel en practica. La app lo necesita para
                # saber si pinta opciones, huecos que se arrastran o parejas.
                'formato_practica': level.formato_practica,
                'es_de_practica': level.es_de_practica,
                'question_count': questions.count(),
                'questions': serializer.data
            })
        except Level.DoesNotExist:
            return Response(
                {'error': f'Nivel {level_id} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
