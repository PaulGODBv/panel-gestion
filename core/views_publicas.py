# -*- coding: utf-8 -*-
"""Lo único del proyecto que se ve sin tener cuenta: la página de presentación.

Vive aparte de `views.py` —que es la API de la app— y de `admin_views.py`
—que son las pantallas del panel— porque no se parece a ninguna de las dos:
no exige sesión, no habla con la app y su público no es la Universidad sino
el estudiante que todavía no se ha instalado nada.

También es la respuesta a un 404: hasta ahora la raíz del sitio no existía, y
el enlace «Volver al sitio» del inicio de sesión llevaba a una página de error.
"""
from __future__ import annotations

import pathlib

from django.conf import settings
from django.templatetags.static import static
from django.views.generic import TemplateView

#: Dónde se deja el APK para que la página lo ofrezca.
#:
#: Va en MEDIA y no en los estáticos a propósito: es un producto de la
#: compilación de la app, no código fuente, y son diez megas que no tienen por
#: qué entrar en el repositorio ni volver a subirse en cada despliegue.
CARPETA_APK = "apk"
NOMBRE_APK = "reta2.apk"

#: Vídeo de presentación.
#:
#: Va en ESTÁTICOS y no en media, al revés que el APK, y la diferencia no es
#: capricho: son 2,8 MB de quince segundos, menos que las dos capturas de
#: teléfono que esta misma página ya sirve. El APK son once y se recompila con
#: cada versión; esto se rinde una vez y cambia como cambia el texto.
#:
#: Estando en estáticos entra en la imagen al construirla, lo sirve WhiteNoise
#: con huella en el nombre y caché inmutable, y sobrevive a los reinicios. En
#: `media/` no sobrevivía: el disco del contenedor es efímero, y además la
#: carpeta está en `.gitignore`, así que el archivo no llegaba siquiera a
#: existir cuando GitHub Actions clona el repositorio para construir.
RUTA_VIDEO = "landing/video/promo-reta2-15s.mp4"


def _archivo_de_medios(ruta_relativa: str) -> pathlib.Path:
    return pathlib.Path(settings.MEDIA_ROOT) / ruta_relativa


class LandingView(TemplateView):
    """Qué es Reta2, cómo se instala y dónde se descarga.

    **La página se adapta a lo que hay.** El APK y el vídeo son archivos que
    se dejan caer en `media/` cuando están listos, y mientras no estén la
    página no enseña un botón roto ni un reproductor vacío: lo dice. Es el
    mismo criterio que en el panel — un hueco explica qué falta, no finge que
    no falta nada.
    """

    template_name = "landing/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Primero la URL externa, si la hay. El archivo local se conserva como
        # respaldo para quien levante esto sin red ni Release publicado.
        url_externa = getattr(settings, "RETA2_APK_URL", "").strip()

        apk = _archivo_de_medios(f"{CARPETA_APK}/{NOMBRE_APK}")
        hay_apk = bool(url_externa) or apk.is_file()

        # `static()` da la ruta con huella —promo-reta2-15s.a1b2c3.mp4— cuando
        # el manifiesto existe, que es en produccion. En desarrollo devuelve la
        # ruta tal cual. Si algun dia se retira el archivo, `static()` lanzaria
        # con el almacenamiento de manifiesto, asi que el fallo se atrapa y la
        # seccion del video desaparece en vez de tumbar la portada entera.
        try:
            video_url = static(RUTA_VIDEO)
        except ValueError:
            video_url = ""

        ctx.update({
            "hay_apk": hay_apk,
            "apk_url": (
                url_externa if url_externa
                else f"{settings.MEDIA_URL}{CARPETA_APK}/{NOMBRE_APK}" if hay_apk
                else ""
            ),
            # En megas y con una cifra decimal: el estudiante decide con esto
            # si lo baja con datos moviles o espera a tener wifi. Del archivo
            # local se mide; de la URL externa se toma del ajuste, porque
            # medirla exigiria una peticion de red en cada carga.
            "apk_megas": (
                getattr(settings, "RETA2_APK_MEGAS", "") or None if url_externa
                else round(apk.stat().st_size / 1048576, 1) if apk.is_file()
                else None
            ),
            "video_url": video_url,
            # Si el video acaba estando en YouTube basta con poner la direccion
            # de insercion en los ajustes; la plantilla prefiere esta.
            "video_incrustado": getattr(settings, "RETA2_VIDEO_PRESENTACION", ""),
        })
        return ctx


def no_disponible(request, exception=None):
    """La pantalla de «esto es solo del superadministrador».

    Reemplaza al manejador de 403 de Django por una razon concreta: el suyo
    dibuja la plantilla con un contexto minimo, y esta extiende la base del
    panel, que necesita el contexto del admin para saber de donde sacar la hoja
    de estilos. Sin eso la pagina sale entera pero sin una sola regla, que es
    exactamente como salio la primera vez.

    El contexto se pide dentro de un `try`: a un 403 tambien se puede llegar
    sin haber iniciado sesion, y ahi `each_context` no tiene de donde tirar.
    Mas vale una pagina sin barra lateral que un error dentro del manejador de
    errores.
    """
    from django.contrib import admin
    from django.shortcuts import render

    contexto = {}
    try:
        contexto = admin.site.each_context(request)
    except Exception:
        pass

    return render(request, "403.html", contexto, status=403)
