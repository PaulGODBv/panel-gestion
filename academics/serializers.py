from rest_framework import serializers
from .models import Competence, Level, Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'text', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    # La app necesita saber a que competencia pertenece la pregunta sin volver
    # a consultar el catalogo; se deduce del nivel, asi que no hace falta una
    # columna aparte que se pueda desincronizar.
    competence_id = serializers.IntegerField(source='level.competence_id', read_only=True)
    context_image_url = serializers.SerializerMethodField()
    context_image_alt = serializers.SerializerMethodField()
    context_image_es_figura = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id',
            'level_id',
            'competence_id',
            'text',
            'options',
            'correct_option_order',
            'explanation',
            'reading_text',
            'context_image_url',
            'context_image_alt',
            'context_image_es_figura',
            'is_active',
            'updated_at',
            # Nombre de drawable heredado. Se sigue enviando mientras haya
            # versiones de la app que lo resuelvan contra el APK.
            'context_image',
        ]

    def _url_absoluta(self, ruta):
        """URL completa si hay peticion en contexto; si no, la relativa.

        La app necesita una URL que pueda pedir tal cual. Con la peticion
        delante se devuelve absoluta —incluye host y puerto—, que es lo que
        hace que funcione desde el telefono.
        """
        peticion = self.context.get('request')
        return peticion.build_absolute_uri(ruta) if peticion else ruta

    def get_context_image_url(self, obj):
        activo = obj.context_asset
        if not (activo and activo.image):
            return None
        return self._url_absoluta(activo.image.url)

    def get_context_image_alt(self, obj):
        return obj.context_asset.alt_text if obj.context_asset else None

    def get_context_image_es_figura(self, obj):
        """Si la app debe tenirla con el color del tema.

        Verdadero para tablas y esquemas, que se ven como parte de la
        aplicacion. Falso para fotografias e historietas, que se muestran tal
        cual: tenirlas de un color plano las destruiria.

        Por defecto verdadero, que es como se comportaban las doce imagenes
        que ya existian.
        """
        return obj.context_asset.es_figura if obj.context_asset else True


class UrlDelIconoMixin:
    """Da la URL absoluta del icono del nivel, o `null` si no tiene.

    Absoluta y no «/api/levels/3/icono/1/» por lo mismo que la imagen de
    contexto: el telefono recibe la respuesta y no sabe contra que host
    resolver un camino suelto. Si falta el `request` en el contexto se
    devuelve el camino relativo, que al menos no es mentira.

    Lleva la version dentro de la ruta a proposito. El icono se sirve con
    cache de un anio, asi que cambiarlo tiene que cambiar la URL; de lo
    contrario la app seguiria enseniando el anterior sin que nadie entienda
    por que.
    """

    def get_icono_url(self, obj):
        if not obj.icono:
            return None
        camino = f"/api/levels/{obj.pk}/icono/{obj.icono_version}/"
        peticion = self.context.get("request")
        return peticion.build_absolute_uri(camino) if peticion else camino


class LevelSerializer(UrlDelIconoMixin, serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()
    icono_url = serializers.SerializerMethodField()

    class Meta:
        model = Level
        fields = [
            'id',
            'name',
            'description',
            'order',
            'is_Locked_by_default',
            'formato_practica',
            'icono_url',
            'question_count',
            'questions'
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class LevelSummarySerializer(UrlDelIconoMixin, serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    icono_url = serializers.SerializerMethodField()

    class Meta:
        model = Level
        fields = [
            'id',
            'name',
            'description',
            'order',
            'is_Locked_by_default',
            'formato_practica',
            'icono_url',
            'question_count'
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class CompetenceSerializer(serializers.ModelSerializer):
    levels = LevelSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Competence
        fields = ['id', 'name', 'description', 'order', 'levels']
