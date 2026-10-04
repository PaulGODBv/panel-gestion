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


class LevelSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Level
        fields = [
            'id',
            'name',
            'description',
            'order',
            'is_Locked_by_default',
            'formato_practica',
            'question_count',
            'questions'
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class LevelSummarySerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Level
        fields = [
            'id',
            'name',
            'description',
            'order',
            'is_Locked_by_default',
            'formato_practica',
            'question_count'
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class CompetenceSerializer(serializers.ModelSerializer):
    levels = LevelSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Competence
        fields = ['id', 'name', 'description', 'order', 'levels']
