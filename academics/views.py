from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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
    def get(self, request):
        competences = Competence.objects.prefetch_related('levels').all()
        serializer = CompetenceSerializer(competences, many=True)
        return Response(serializer.data)


class QuestionsByLevelView(APIView):
    """
    GET /api/questions/<level_id>/
    Devuelve todas las preguntas de un nivel con sus opciones
    """
    def get(self, request, level_id):
        try:
            level = Level.objects.get(id=level_id)
            questions = Question.objects.prefetch_related('options').filter(level=level)
            serializer = QuestionSerializer(questions, many=True)
            return Response({
                'level_id': level_id,
                'level_name': level.name,
                'question_count': questions.count(),
                'questions': serializer.data
            })
        except Level.DoesNotExist:
            return Response(
                {'error': f'Nivel {level_id} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
