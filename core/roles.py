# -*- coding: utf-8 -*-
"""Los dos papeles del panel, y qué separa uno de otro.

Hasta ahora solo había superadministradores: todo el que entraba podía hacerlo
todo, incluido crear cuentas y borrar una competencia entera con sus niveles y
sus preguntas detrás.

**La diferencia es exactamente dos cosas**, decididas por el usuario el
13/10/2026:

1. El administrador **no gestiona las cuentas del panel**. Es lo que define a
   un superadministrador y lo único que no se delega.
2. El administrador **no borra nada**. Puede crear y editar, que es trabajar de
   verdad, pero no destruir. Importa más de lo que parece: borrar una
   competencia se lleva por delante sus niveles y sus preguntas en cascada, y
   eso no se deshace desde ninguna pantalla.

Todo lo demás —el banco de preguntas, las métricas, las fichas de estudiante y
los datos crudos— lo comparten. El panel no cambia según quién entre; lo que
cambia es qué deja hacer.

CÓMO SE APLICA
--------------
Con el sistema de permisos de Django y un grupo, no con comprobaciones
sueltas repartidas por las vistas. Así el propio admin esconde los botones de
borrar en vez de enseñarlos y fallar al pulsarlos, que es la diferencia entre
una interfaz que se explica y una que castiga.

Se ejecuta en `post_migrate` y no en una migración de datos porque los
permisos los crea Django **al final** de `migrate`: una migración de datos
corriendo en esa misma pasada no encontraría ninguno y crearía un grupo vacío
sin avisar.
"""
from __future__ import annotations

GRUPO_ADMIN = "Administradores"

#: Lo que el administrador puede hacer, por modelo.
#:
#: `delete` no está en ninguna línea, y no por olvido. Los modelos de `auth`
#: tampoco aparecen: ahí está la raya entre los dos papeles.
PERMISOS = {
    "academics": {
        "competence": ("view", "add", "change"),
        "level": ("view", "add", "change"),
        "question": ("view", "add", "change"),
        "questionoption": ("view", "add", "change"),
        "contextasset": ("view", "add", "change"),
        # El historial se consulta, no se fabrica.
        "historicalquestion": ("view",),
    },
    "core": {
        # Los reportes llegan de la app y son la fuente de los datos: se miran,
        # no se corrigen a mano. Editarlos seria falsear la medicion.
        "studentreport": ("view",),
        "levelprogressreport": ("view",),
        "visitaguiada": ("view", "change"),
    },
}


def asegurar_roles(**kwargs) -> None:
    """Crea o actualiza el grupo. Idempotente: se llama en cada `migrate`.

    Reasigna el conjunto entero en vez de añadir lo que falte, para que quitar
    una línea de PERMISOS retire el permiso de verdad. Un grupo que solo crece
    acaba dando acceso que nadie recuerda haber concedido.
    """
    from django.contrib.auth.models import Group, Permission

    codigos = []
    for app, modelos in PERMISOS.items():
        for modelo, acciones in modelos.items():
            for accion in acciones:
                codigos.append((app, f"{accion}_{modelo}"))

    permisos = list(
        Permission.objects.filter(
            content_type__app_label__in=[a for a, _ in codigos],
            codename__in=[c for _, c in codigos],
        ).select_related("content_type")
    )

    # El filtro de arriba cruza apps y codigos, asi que se afina aqui: sin esto
    # un `view_question` de otra aplicacion entraria por la puerta de atras.
    esperados = set(codigos)
    permisos = [
        p for p in permisos
        if (p.content_type.app_label, p.codename) in esperados
    ]

    grupo, _ = Group.objects.get_or_create(name=GRUPO_ADMIN)
    grupo.permissions.set(permisos)


def es_superadmin(usuario) -> bool:
    """Quien gestiona las cuentas del panel.

    Se pregunta por `is_superuser` y no por pertenencia a un grupo: el grupo
    describe lo que alguien puede hacer, pero ser superadministrador es una
    propiedad de la cuenta y Django ya la trata como tal en todas partes.
    """
    return bool(usuario and usuario.is_authenticated and usuario.is_superuser)


# ---------------------------------------------------------------------------
# Los nombres de los permisos, en español
# ---------------------------------------------------------------------------
#
# Django los genera como «Can add» + el nombre del modelo y los **guarda en la
# base**, no los traduce al mostrarlos. Por eso el catalogo de traduccion no
# sirve aqui y salian cosas como «Can add Competencia»: medio en ingles y medio
# en español, en la misma linea.
#
# Esto los reescribe. Es un dato, no codigo, asi que se puede volver atras
# borrando la fila y corriendo `migrate`.

ACCIONES = {
    "add": "Puede añadir",
    "change": "Puede editar",
    "delete": "Puede eliminar",
    "view": "Puede ver",
}


def traducir_permisos(**kwargs) -> None:
    """Pone en español el nombre de los permisos estandar.

    Solo toca los cuatro que genera Django por modelo. Un permiso propio, con
    un `codename` que no empiece por una de esas cuatro acciones, se deja como
    lo escribio quien lo creo: ahi el nombre es suyo y no de una plantilla.
    """
    from django.conf import settings
    from django.contrib.auth.models import Permission
    from django.utils import translation

    cambiados = []

    # Sin activar el idioma, los `verbose_name` de los modelos del propio
    # Django —que son cadenas perezosas traducibles— se resuelven en ingles:
    # `post_migrate` corre fuera de cualquier peticion y ahi no hay idioma
    # activo. Salia «Puede añadir group» en vez de «Puede añadir grupo».
    with translation.override(settings.LANGUAGE_CODE):
        for permiso in Permission.objects.select_related("content_type"):
            accion = permiso.codename.split("_")[0]
            etiqueta = ACCIONES.get(accion)
            if not etiqueta:
                continue

            modelo = permiso.content_type.model_class()
            # Un tipo de contenido puede quedar huerfano si su modelo
            # desaparecio; ahi no hay verbose_name que leer.
            nombre = (
                str(modelo._meta.verbose_name) if modelo
                else permiso.content_type.model
            )

            # Mayuscula inicial: los verbose_name se escriben en minuscula por
            # convencion de Django y aqui empiezan frase.
            nuevo = f"{etiqueta} {nombre[:1].lower()}{nombre[1:]}"
            if permiso.name != nuevo:
                permiso.name = nuevo
                cambiados.append(permiso)

    if cambiados:
        Permission.objects.bulk_update(cambiados, ["name"])
