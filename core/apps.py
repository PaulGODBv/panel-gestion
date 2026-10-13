from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        """Mantiene al dia el grupo «Administradores» y los nombres de permisos.

        **Sin `sender`, y eso es lo importante.** Django crea los permisos de
        cada aplicacion en su propio `post_migrate`, y los recorre en el orden
        de INSTALLED_APPS. Enganchando esto a `sender=self` corria justo
        despues de las migraciones de `core` — cuando los permisos de
        `academics` todavia no existen.

        En esta maquina no se noto nunca, porque `migrate` se habia corrido
        muchas veces y la segunda pasada ya encontraba todo. Se vio al levantar
        el contenedor contra una base **recien creada**, que es exactamente lo
        que sera el despliegue: el grupo salio con 4 permisos de 20 y 24
        nombres sin traducir. Un administrador recien creado no habria podido
        hacer nada.

        Sin `sender` se ejecuta una vez por aplicacion migrada. Las dos
        funciones son idempotentes y baratas, y lo que importa es que la ultima
        pasada ve ya todos los permisos.
        """
        from .roles import asegurar_roles, traducir_permisos

        post_migrate.connect(asegurar_roles, dispatch_uid='reta2_roles')
        post_migrate.connect(traducir_permisos, dispatch_uid='reta2_permisos')
