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
    
class ContextAsset(models.Model):
    """Imagen de contexto de una pregunta, como archivo.

    Es una entidad aparte y no un campo de Question porque varias preguntas
    comparten la misma imagen: en el banco actual, la tabla de sismos la usan
    cinco preguntas y el esquema de herederos dos. Subirla una vez y
    referenciarla evita duplicar el archivo y, sobre todo, evita que corregir
    una imagen obligue a repetir la correccion en cada pregunta.
    """

    image = models.ImageField(
        upload_to="question-context/",
        verbose_name="Imagen",
    )
    alt_text = models.CharField(
        max_length=180,
        verbose_name="Texto alternativo",
        help_text="Que se ve en la imagen. Lo lee en voz alta el lector de "
                  "pantalla, asi que describe el contenido, no el archivo.",
    )
    caption = models.CharField(
        max_length=240,
        blank=True,
        verbose_name="Leyenda",
        help_text="Opcional. Se muestra debajo de la imagen.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Imagen de contexto"
        verbose_name_plural = "Imagenes de contexto"
        ordering = ["alt_text"]

    def __str__(self):
        return self.alt_text or self.image.name


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
    
    context_asset = models.ForeignKey(
        ContextAsset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions",
        verbose_name="Imagen de contexto",
    )

    # Nombre del drawable dentro del APK, que es como funcionaba antes de que
    # las imagenes fueran archivos. Se conserva mientras haya versiones de la
    # app que lo resuelvan con getIdentifier(); las nuevas usan context_asset.
    # Al retirar esas versiones, esta columna se puede eliminar.
    context_image = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Imagen de contexto (nombre heredado)",
        help_text="Obsoleto. Usa el campo de arriba, que admite subir el archivo.",
    )
    
    explanation = models.TextField(
        blank=True,
        verbose_name="Explicación"
    )
    
    correct_option_order = models.PositiveIntegerField(
        verbose_name="Orden de la opción correcta",
        help_text="Posicion (1-4) de la opción correcta en la lista"
    )
    
    # La app retira una pregunta desactivandola, no borrandola: el progreso del
    # estudiante apunta a su id, y borrar la fila dejaria intentos huerfanos.
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Si se desmarca, la pregunta deja de enviarse a la app sin "
                  "romper los intentos ya registrados.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    # Marca de cambio: es el cursor con el que la app pide solo lo nuevo.
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultima modificacion")
    
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