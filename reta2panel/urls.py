"""
URL configuration for reta2panel project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from core.views_publicas import LandingView, no_disponible

urlpatterns = [
    # La raiz del sitio. Hasta ahora no existia: daba un 404 y dejaba roto el
    # enlace "Volver al sitio" del inicio de sesion.
    path('', LandingView.as_view(), name='landing'),
    path('admin/', admin.site.urls),
    path('panel/', include('core.urls_admin')),
    path('api/', include('academics.urls')),
    path('api/', include('core.urls')),
]

# En desarrollo sirve Django las imagenes subidas. En produccion esto no actua:
# static() solo devuelve rutas con DEBUG activo, y ahi las sirve el servidor
# web o el CDN que se ponga delante.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Que un administrador llegue a algo del superadministrador no es un error del
# servidor: es una frase. El manejador propio esta para que esa frase salga con
# los estilos del panel y no como texto suelto.
handler403 = no_disponible
