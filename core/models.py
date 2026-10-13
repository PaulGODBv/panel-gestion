from django.db import models

# Create your models here.

class StudentReport(models.Model):
    username = models.CharField(max_length=150, verbose_name="Usuario")
    email = models.CharField(max_length=254, blank=True, verbose_name="Correo")
    
    total_questions_answered = models.PositiveIntegerField(default=0, verbose_name="Preguntas respondidas")
    total_practice_time_seconds = models.PositiveIntegerField(default=0, verbose_name="Tiempo de práctica (s)")
    current_streak_days = models.PositiveIntegerField(default=0, verbose_name="Racha actual (días)")
    # La racha viva se reinicia al romperse; esta no. Es contra la que se miden
    # los logros de racha, igual que en la app: un logro conseguido no se
    # devuelve. Default 0 para los reportes anteriores al campo.
    max_streak_days = models.PositiveIntegerField(default=0, verbose_name="Mejor racha")
    daily_practice_time_seconds = models.PositiveIntegerField(default=0, verbose_name="Tiempo de hoy (s)")
    
    reported_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del reporte")
    app_version = models.CharField(max_length=20, blank=True, verbose_name="Versión de la app")
    academic_program = models.CharField(max_length=100, blank=True, null=True, verbose_name="Programa Académico")
    
    class Meta:
        verbose_name = 'Reporte de Estudiante'
        verbose_name_plural = 'Reportes de Estudiantes'
        ordering = ['-reported_at']
        
    def __str__(self):
        return f"{self.username} - {self.reported_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @property
    def practice_time_formatted(self):
        total = self.total_practice_time_seconds
        hours = total // 3600
        minutes = (total % 3600) // 60
        return f"{hours}h {minutes}m"

    @property
    def risk_status(self):
        from django.utils import timezone
        import datetime
        now = timezone.now()
        
        # 1. Inactive: more than 7 days since last sync
        if (now - self.reported_at).days > 7:
            return 'inactivo'
        
        # 2. At risk: current streak is 0, but total practice time is somewhat high indicating they used to practice (or we could use a history model to strictly check "had streak > 5"). Since we don't have historical streaks, we will estimate: if they answered a lot of questions but streak is 0, they lost it. Let's use a simple heuristic for now as requested: "cuya racha cayó a 0 después de haber tenido más de 5 días" - Since we only have current report, maybe we assume if they have > 50 total questions and streak is 0. 
        # But wait! We have all reports for the user? Actually StudentReport is just one row per sync, or is it one row per user updated?
        # Let's check how StudentReport is used. If it's a log, we need to query previous reports.
        # "cuya racha cayó a 0 después de haber tenido más de 5 días"
        # Let's query previous reports for this user:
        if self.current_streak_days == 0:
            previous_max_streak = StudentReport.objects.filter(username=self.username).exclude(id=self.id).aggregate(models.Max('current_streak_days'))['current_streak_days__max']
            if previous_max_streak and previous_max_streak > 5:
                return 'en_riesgo'
        
        # Default: Active
        return 'activo'

    
class LevelProgressReport(models.Model):
    report = models.ForeignKey(
        StudentReport,
        on_delete=models.CASCADE,
        related_name='level_progress',
        verbose_name="Reporte",
    )
    
    competence_name = models.CharField(max_length=100, verbose_name="Competencia")
    level_name = models.CharField(max_length=100, verbose_name="Nivel")
    competence_id = models.PositiveIntegerField(verbose_name="Id de competencia")
    level_id = models.PositiveIntegerField(verbose_name="Id de nivel")
    score = models.PositiveIntegerField(default=0, verbose_name="Aciertos")
    total_questions = models.PositiveIntegerField(default=0, verbose_name="Preguntas")
    is_completed = models.BooleanField(default=False, verbose_name="Completado")
    time_spent_seconds = models.PositiveIntegerField(default=0, verbose_name="Tiempo dedicado (s)")
    
    class Meta:
        verbose_name = "Progreso por nivel"
        verbose_name_plural = "Progresos por nivel"
        
    def __str__(self):
        return f"{self.report.username} - {self.level_name}"
    
    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 2)

class VisitaGuiada(models.Model):
    """Qué pasos de los primeros pasos lleva dados cada persona del panel.

    Una fila por usuario. Vive en la base y no en el navegador a proposito: con
    `localStorage` la visita se repetiria al cambiar de equipo y desapareceria
    al limpiar el historial, que son dos formas de mentir sobre si alguien ya
    la vio.

    Los pasos se guardan como claves separadas por comas y no en una tabla
    aparte ni en un JSONField: son cuatro, caben en una linea, y una tabla de
    relacion para esto seria mas esquema que dato.
    """

    usuario = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='visita_guiada',
        verbose_name="Usuario",
    )

    pasos = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name="Pasos dados",
        help_text="Claves separadas por comas.",
    )

    cerrada = models.BooleanField(
        default=False,
        verbose_name="Cerrada a mano",
        help_text="Si se desmarca, la tarjeta de primeros pasos vuelve a salir.",
    )

    creada_en = models.DateTimeField(auto_now_add=True, verbose_name="Primera vez")
    actualizada_en = models.DateTimeField(auto_now=True, verbose_name="Ultimo paso")

    class Meta:
        verbose_name = "Visita guiada"
        verbose_name_plural = "Visitas guiadas"

    def __str__(self):
        return f"{self.usuario} - {self.pasos or 'sin empezar'}"

    def _lista(self):
        return [p for p in self.pasos.split(',') if p]

    def hechos(self, paso: str) -> bool:
        return paso in self._lista()

    def anotar(self, paso: str) -> None:
        if self.hechos(paso):
            return
        actuales = self._lista()
        actuales.append(paso)
        self.pasos = ','.join(actuales)
        self.save(update_fields=['pasos', 'actualizada_en'])
