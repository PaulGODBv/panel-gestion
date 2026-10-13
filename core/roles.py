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
