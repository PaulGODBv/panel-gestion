from django.db import models

# Create your models here.

class StudentReport(models.Model):
    username = models.CharField(max_length=150)
    email = models.CharField(max_length=254, blank=True)
    
    total_questions_answered = models.PositiveIntegerField(default=0)
    total_practice_time_seconds= models.PositiveIntegerField(default=0)
    current_streak_days = models.PositiveIntegerField(default=0)
    daily_practice_time_seconds = models.PositiveIntegerField(default=0)
    
    reported_at = models.DateTimeField(auto_now_add=True)
    app_version = models.CharField(max_length=20, blank=True)
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
        related_name='level_progress'
    )
    
    competence_name = models.CharField(max_length=100)
    level_name = models.CharField(max_length=100)
    competence_id = models.PositiveIntegerField()
    level_id = models.PositiveIntegerField()
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    
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