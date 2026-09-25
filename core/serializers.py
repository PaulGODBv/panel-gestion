from rest_framework import serializers
from .models import StudentReport, LevelProgressReport


# Dominio de correo institucional aceptado para registrar estudiantes.
# Si la universidad usa otro dominio, este es el único punto a cambiar.
INSTITUTIONAL_EMAIL_DOMAIN = "@mail.udes.edu.co"


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

    # El modelo permite el correo en blanco, pero en la sincronización es
    # obligatorio: es el dato que permite comprobar que quien envía el reporte
    # se registró con una cuenta institucional.
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = StudentReport
        fields = [
            'username',
            'email',
            'total_questions_answered',
            'total_practice_time_seconds',
            'current_streak_days',
            'daily_practice_time_seconds',
            # La app envia academic_program desde el registro del estudiante.
            # Sin este campo en la lista, DRF lo descartaba en silencio y el
            # panel mostraba vacia la comparativa por programa academico.
            'academic_program',
            'app_version',
            'level_progress'
        ]

    def validate_email(self, value):
        """Solo se aceptan reportes de cuentas del dominio institucional.

        La app Android hace esta misma comprobación en el registro para dar
        respuesta inmediata; esta validación es la que realmente protege los
        datos, porque el endpoint es público y puede recibir cualquier payload.
        """
        email = value.strip()

        if not email.lower().endswith(INSTITUTIONAL_EMAIL_DOMAIN):
            raise serializers.ValidationError(
                "Por favor, regístrate utilizando tu correo institucional "
                f"({INSTITUTIONAL_EMAIL_DOMAIN})."
            )

        return email

    def create(self, validated_data):
        level_progress_data = validated_data.pop('level_progress', [])

        report = StudentReport.objects.create(**validated_data)

        for progress_data in level_progress_data:
            LevelProgressReport.objects.create(
                report=report,
                **progress_data
            )

        return report
