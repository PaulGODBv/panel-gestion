import pathlib

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

    # Como se juega el nivel cuando es de practica (order = 0).
    #
    # Va en el nivel y no en la pregunta porque describe la **forma de
    # interactuar**, no el contenido: las mismas preguntas de siempre se pueden
    # presentar de las tres maneras sin cambiar un solo dato.
    #
    # Y no hace falta inventar ningun campo mas, porque el banco ya tiene la
    # forma que piden los dos formatos nuevos:
    #
    # - ARRASTRAR: una frase con un hueco y cuatro candidatas es exactamente
    #   una pregunta de opcion unica. Arrastrar la palabra al hueco en vez de
    #   tocar una opcion es presentacion, no datos.
    # - UNIR: las cinco preguntas de "Feelings" comparten las mismas ocho
    #   opciones y cada una tiene una correcta distinta. Eso ya es una rejilla
    #   de parejas: enunciados a un lado, respuestas al otro, y las que sobran
    #   hacen de distractores.
    FORMATO_OPCION = "opcion"
    FORMATO_ARRASTRAR = "arrastrar"
    FORMATO_UNIR = "unir"
    FORMATOS_DE_PRACTICA = [
        (FORMATO_OPCION, "Elegir una opcion (como en evaluacion)"),
        (FORMATO_ARRASTRAR, "Arrastrar la palabra al hueco"),
        (FORMATO_UNIR, "Unir parejas"),
    ]

    formato_practica = models.CharField(
        max_length=12,
        choices=FORMATOS_DE_PRACTICA,
        default=FORMATO_OPCION,
        verbose_name="Formato en practica",
        help_text="Solo se aplica a los niveles de practica (orden 0). En los "
                  "de evaluacion se ignora: ahi siempre se elige una opcion.",
    )

    @property
    def es_de_practica(self):
        """Los niveles de practica son los de orden 0, delante del basico."""
        return self.order == 0

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

    # Las cartillas llegan escaneadas y pesan: los doce PNG iniciales sumaban
    # 1,8 MB para 12 imagenes. Como ahora viajan al telefono en cada
    # sincronizacion, se normalizan al guardar en vez de confiar en que quien
    # sube el contenido las optimice.
    ANCHO_MAXIMO = 1600
    CALIDAD_WEBP = 82

    # Rampa de luminancia a alfa al despegar la figura del papel. Por encima de
    # BLANCO es fondo y desaparece; por debajo de NEGRO es trazo pleno. El tramo
    # de en medio conserva el suavizado de los bordes.
    BLANCO = 243
    NEGRO = 60
    MARGEN = 8

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            self._normalizar_a_webp()

    @classmethod
    def _ya_es_figura(cls, img):
        """Una figura ya tratada llega con fondo transparente.

        Vuelve a pasarle el matiz a una figura ya tratada y sale un rectangulo
        negro: `convert("RGB")` aplana lo transparente a negro, la luminancia da
        cero en todas partes y el alfa sale opaco entero. Por eso esta
        comprobacion no es una optimizacion, es lo que hace que guardar dos
        veces no destruya la imagen.
        """
        return img.mode == "RGBA" and img.getchannel("A").getextrema()[0] == 0

    @classmethod
    def _a_figura(cls, img):
        """Blanco del papel a transparencia, trazo a tinta negra, recorte al contenido.

        La app pinta esto sobre su propia superficie y lo tine segun el tema:
        tinta oscura en claro, clara en oscuro. Asi la figura se ve como parte
        de la app y no como el recorte de una guia impresa, que es lo que se
        veia en modo oscuro.
        """
        from PIL import Image, ImageOps

        luz = ImageOps.grayscale(img.convert("RGB"))
        alfa = luz.point(
            lambda v: 0 if v >= cls.BLANCO else (
                255 if v <= cls.NEGRO
                else int(255 * (cls.BLANCO - v) / (cls.BLANCO - cls.NEGRO))
            )
        )
        tinta = Image.new("RGBA", img.size, (0, 0, 0, 255))
        tinta.putalpha(alfa)

        caja = alfa.getbbox()
        if caja is None:
            return tinta
        izq, arr, der, aba = caja
        return tinta.crop((
            max(0, izq - cls.MARGEN),
            max(0, arr - cls.MARGEN),
            min(tinta.width, der + cls.MARGEN),
            min(tinta.height, aba + cls.MARGEN),
        ))

    def _normalizar_a_webp(self):
        """Reescribe la imagen como figura WebP con alfa y borra el original."""
        from io import BytesIO

        from django.core.files.base import ContentFile
        from PIL import Image

        original = self.image.name
        try:
            self.image.open()
            try:
                img = Image.open(self.image)
                # load() lee el archivo entero: a partir de aqui la imagen ya
                # no depende del descriptor, y en Windows hay que cerrarlo
                # antes de borrar el original o el sistema no deja.
                img.load()
            finally:
                self.image.close()
        except Exception:
            # Un archivo ilegible no debe impedir guardar la ficha: se queda
            # como esta y se ve en el admin que algo no cuadra.
            return

        ya_tratada = self._ya_es_figura(img)
        if ya_tratada and original.lower().endswith(".webp"):
            # Nada que hacer: ya esta en el formato y con el fondo que toca.
            return

        if img.width > self.ANCHO_MAXIMO:
            alto = round(img.height * self.ANCHO_MAXIMO / img.width)
            img = img.resize((self.ANCHO_MAXIMO, alto), Image.LANCZOS)

        if not ya_tratada:
            img = self._a_figura(img)
        elif img.mode != "RGBA":
            img = img.convert("RGBA")

        buffer = BytesIO()
        # Sin perdida: son lineas y texto, donde el ruido de la compresion se
        # nota mucho mas que en una foto, y ademas suele ocupar menos.
        img.save(buffer, "WEBP", lossless=True, method=6)

        nombre = pathlib.PurePath(original).stem + ".webp"
        self.image.save(nombre, ContentFile(buffer.getvalue()), save=False)
        super().save(update_fields=["image"])

        # El original ya no lo referencia nadie.
        if original != self.image.name:
            self.image.storage.delete(original)


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