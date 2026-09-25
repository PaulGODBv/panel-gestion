"""Autenticación de la API que consume la aplicación Android.

El panel expone `/api/reports/sync/` y `/api/ranking/` a la red local para que
la app envíe el progreso de cada estudiante. Sin autenticación, cualquiera que
conozca la URL puede insertar reportes falsos o leer el ranking completo.

Para el alcance de este proyecto se usa una clave estática compartida entre la
app y el panel, enviada en la cabecera `X-API-Key`. Es la opción más simple que
cierra el agujero; conviene saber qué protege y qué no:

- Impide que un tercero cualquiera escriba en el panel desde la red.
- NO identifica al estudiante: la clave viaja dentro del APK y puede extraerse
  descompilándolo, así que quien tenga la app tiene la clave.
- Sobre HTTP la cabecera viaja en claro. En un despliegue real haría falta
  HTTPS y credenciales por usuario (token por sesión, JWT u OAuth).
"""

import hmac

from django.conf import settings
from rest_framework.permissions import BasePermission

API_KEY_HEADER = "X-API-Key"


class HasValidApiKey(BasePermission):
    """Exige la cabecera `X-API-Key` con el valor de `settings.RETA2_API_KEY`."""

    message = (
        "Falta la clave de API o no es válida. "
        f"Envía la cabecera {API_KEY_HEADER}."
    )

    def has_permission(self, request, view):
        expected = getattr(settings, "RETA2_API_KEY", "")

        # Sin clave configurada no se acepta nada: es preferible que la
        # sincronización falle de forma evidente a dejar el endpoint abierto.
        if not expected:
            return False

        provided = request.headers.get(API_KEY_HEADER, "")

        # Comparación en tiempo constante: evita distinguir una clave casi
        # correcta de una equivocada midiendo cuánto tarda la respuesta.
        return hmac.compare_digest(provided, expected)
