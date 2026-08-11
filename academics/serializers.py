from rest_framework import serializers
from .models import Competence, Level, Question, QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'text', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            'id',
            'text',
            'options',
            'correct_option_order',
            'explanation',
            'reading_text',
            'context_image'
        ]


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
            'question_count'
        ]

    def get_question_count(self, obj):
        return obj.questions.count()


class CompetenceSerializer(serializers.ModelSerializer):
    levels = LevelSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Competence
        fields = ['id', 'name', 'description', 'order', 'levels']
