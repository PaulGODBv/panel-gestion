from django.db import models
from simple_history.models import HistoricalRecords

# Create your models here.
class Competence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveBigIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Competencia'
        verbose_name_plural = 'Competencias'
        
    def __str__(self):
        return self.name
    

class Level(models.Model):
    competence = models.ForeignKey(
        Competence, 
        on_delete=models.CASCADE, 
        related_name='levels'
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    order = models.PositiveBigIntegerField(default=0)
    is_Locked_by_default = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Nivel'
        verbose_name_plural = 'Niveles'
    def __str__(self):
        return f"{self.competence.name} - {self.name}"
    
class Question(models.Model):
    history = HistoricalRecords()
    level = models.ForeignKey(
        Level, 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    
    text = models.TextField(verbose_name="Enunciado")
    reading_text = models.TextField(
        blank=True,
        verbose_name="Texto de lectura"
    )
    
    context_image = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Imagen de contexto"
    )
    
    explanation = models.TextField(
        blank=True,
        verbose_name="Explicación"
    )
    
    correct_option_order = models.PositiveIntegerField(
        verbose_name="Orden de la opción correcta",
        help_text="Posicion (1-4) de la opción correcta en la lista"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'
        
    def __str__(self):
        return f"{self.level} - {self.text[:60]}..."
    
class QuestionOption(models.Model):
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='options'
    )
    
    text = models.TextField(verbose_name="Texto de la opcion")
    order = models.PositiveIntegerField(verbose_name="Orden")
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Opcion'
        verbose_name_plural = 'Opciones'
    
    def __str__(self):
        return f"Opcion {self.order}: {self.text[:40]}"