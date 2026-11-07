from django.http import Http404, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
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
        # El contexto con la peticion, por lo mismo que en las preguntas: sin
        # el, `icono_url` sale como «/api/levels/1/icono/1/» y el telefono no
        # sabe contra que host resolverlo. Con el, sale la direccion entera.
        serializer = CompetenceSerializer(
            competences, many=True, context={'request': request}
        )
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


class IconoDeNivelView(APIView):
    """GET /api/levels/<id>/icono/ — el PNG del icono, o 404 si no tiene.

    Sirve bytes de la base y no un archivo de `media/`, por lo que explica el
    campo `Level.icono`: el disco del contenedor es efimero y lo que se suba
    ahi no sobrevive al siguiente reinicio.

    **Se cachea un anio y se declara inmutable.** Suena agresivo para algo que
    el profesor puede cambiar, y por eso la URL lleva dentro `icono_version`:
    al subir un icono nuevo la version sube, la URL cambia, y la anterior deja
    de pedirse. Es la misma idea que la huella en el nombre de los estaticos.
    Sin esto, la app seguiria enseniando el icono viejo durante dias y nadie
    sabria por que.
    """

    # La clave de la API **o** una sesion de administrador. Las dos, porque
    # esta URL la piden dos clientes distintos: la app, que manda la cabecera,
    # y el propio panel, que ensenia la miniatura en la lista de niveles desde
    # el navegador y ahi no hay cabecera que valga, solo la cookie de sesion.
    # Sin el `IsAdminUser` la miniatura salia rota con un 403.
    permission_classes = [HasValidApiKey | IsAdminUser]

    def get(self, request, level_id: int, version: int = 0):
        try:
            nivel = Level.objects.only("icono", "icono_version").get(pk=level_id)
        except Level.DoesNotExist:
            raise Http404(f"Nivel {level_id} no encontrado")

        if not nivel.icono:
            raise Http404(f"El nivel {level_id} no tiene icono")

        respuesta = HttpResponse(bytes(nivel.icono), content_type="image/png")
        respuesta["Cache-Control"] = "public, max-age=31536000, immutable"
        return respuesta
