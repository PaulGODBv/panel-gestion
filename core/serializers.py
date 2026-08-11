from rest_framework import serializers
from .models import StudentReport, LevelProgressReport


class LevelProgressReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelProgressReport
        fields = [
            'competence_name',
            'level_name',
            'competence_id',
            'level_id',
            'score',
            'total_questions',
            'is_completed',
            'time_spent_seconds'
        ]


class StudentReportSerializer(serializers.ModelSerializer):
    level_progress = LevelProgressReportSerializer(many=True, required=False)

    class Meta:
        model = StudentReport
        fields = [
            'username',
            'email',
            'total_questions_answered',
            'total_practice_time_seconds',
            'current_streak_days',
            'daily_practice_time_seconds',
            'app_version',
            'level_progress'
        ]

    def create(self, validated_data):
        level_progress_data = validated_data.pop('level_progress', [])

        report = StudentReport.objects.create(**validated_data)

        for progress_data in level_progress_data:
            LevelProgressReport.objects.create(
                report=report,
                **progress_data
            )

        return report
