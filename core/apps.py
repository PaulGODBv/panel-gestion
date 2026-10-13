from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        """Mantiene al dia el grupo «Administradores» en cada `migrate`.

        Va en `post_migrate` y no en una migracion de datos porque los permisos
        los crea Django **al final** de `migrate`: una migracion de datos
        corriendo en esa misma pasada no encontraria ninguno y dejaria un grupo
        vacio sin avisar de nada.
        """
        from .roles import asegurar_roles, traducir_permisos

        post_migrate.connect(asegurar_roles, sender=self)
        post_migrate.connect(traducir_permisos, sender=self)
