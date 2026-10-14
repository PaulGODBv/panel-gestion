"""
WSGI config for reta2panel project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reta2panel.settings')

application = get_wsgi_application()


# Las imagenes de contexto de las preguntas viven en `media/` y viajan dentro
# de la imagen del contenedor. En produccion no las servia nadie: el `static()`
# de urls.py solo devuelve rutas con DEBUG activo, y alli se daba por supuesto
# un servidor web por delante. En Container Apps no lo hay —el contenedor es el
# servidor—, asi que las 23 preguntas con imagen la pedian y recibian un 404.
#
# WhiteNoise ya esta en la cadena para los estaticos; aqui se le anade el
# directorio de medios con su prefijo. Es justo el caso para el que vale:
# ficheros que se recorren una vez al arrancar porque no cambian mientras el
# proceso vive.
#
# AVISO: el disco del contenedor es efimero. Una imagen subida por el panel se
# sirve hasta el siguiente reinicio y entonces desaparece. Las que hay aqui
# aguantan porque vienen dentro de la imagen. Para subirlas en caliente hace
# falta almacenamiento externo (Azure Blob Storage).
from django.conf import settings  # noqa: E402  (requiere los ajustes ya cargados)

if settings.MEDIA_ROOT and os.path.isdir(settings.MEDIA_ROOT):
    from whitenoise import WhiteNoise

    application = WhiteNoise(
        application,
        root=str(settings.MEDIA_ROOT),
        # WhiteNoise le pone las barras que falten, asi que `media/` vale.
        prefix=settings.MEDIA_URL,
    )
