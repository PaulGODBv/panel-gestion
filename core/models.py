from django.db import models

# Create your models here.

class StudentReport(models.Model):
    username = models.CharField(max_lenght=150)
    email = models.CharField(max_length=254, blank=true)
    
    total_questions_answered = models.PositiveIntegerField(default=0)
    total_practice_time_seconds= models.PositiveIntegerField(default=0)
    current_streak_days = models.PositiveIntegerField(default=0)
    daily_practice_time_seconds = models.PositiveIntegerField(default=0)
    
    reported_at = models.DateTimeField(auto_now_add=True)
    app_version = models.CharField(max_length=20, blank=True)
    
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