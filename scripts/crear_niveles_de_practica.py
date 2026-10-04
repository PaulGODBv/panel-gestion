# -*- coding: utf-8 -*-
"""Crea el nivel de practica de cada competencia, delante del basico.

Viene de la reunion con el profesor: separar **evaluacion** —lo que ya existe—
de **practica**, con items mas cortos y faciles y el porque al momento.

Por que un nivel y no una categoria nueva: una categoria obliga a tocar el
esquema en los dos lados y a repensar progreso, desbloqueo y ranking. Un nivel
con `order = 0` delante del basico cabe en el modelo que ya hay y no mueve
ninguna columna. La idea es del usuario y es la correcta.

El id que usara la app sale de `generateLevelId(competencia, 0)` =
`competencia * 100`, o sea 100, 200, 300 y 400. No chocan con los 101..403 que
ya existen, y **terminar en 00 es lo que marca un nivel como de practica**
dentro de la app.

Uso:
    python scripts/crear_niveles_de_practica.py            # ensayo
    python scripts/crear_niveles_de_practica.py --aplicar  # escribe, con copia
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import django

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reta2panel.settings")
os.environ.setdefault("RETA2_API_KEY", "solo-para-este-script")
django.setup()

from academics.models import Competence, Level  # noqa: E402

NOMBRE = "Calentamiento"
DESCRIPCION = ("Items cortos para coger ritmo. No cuenta para desbloquear: "
               "al responder te dice si acertaste y por que.")


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    competencias = list(Competence.objects.order_by("order"))

    if not competencias:
        print("No hay competencias. Se aborta.")
        return 1

    pendientes = []
    for c in competencias:
        ya = Level.objects.filter(competence=c, order=0).first()
        if ya:
            print(f"  {c.name[:28]:28} ya tiene nivel de practica (pk={ya.id}), se omite")
        else:
            pendientes.append(c)
            print(f"  {c.name[:28]:28} -> se creara '{NOMBRE}' con order=0, "
                  f"id de app {c.order * 100}")

    if not pendientes:
        print("\nNada que hacer.")
        return 0

    if not aplicar:
        print("\nEnsayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    respaldo = BASE / f"db-antes-practica-{datetime.now():%Y%m%d-%H%M}.sqlite3"
    shutil.copy2(BASE / "db.sqlite3", respaldo)
    print(f"\nCopia de seguridad: {respaldo.name}")

    print("\nCreados:")
    for c in pendientes:
        nivel = Level.objects.create(
            competence=c,
            name=NOMBRE,
            description=DESCRIPCION,
            order=0,
            # Nunca bloqueado: practicar es la puerta de entrada, no un premio.
            is_Locked_by_default=False,
        )
        print(f"  pk={nivel.id:3} competencia {c.order} ({c.name[:24]}) -> id de app {c.order * 100}")

    print("\nFalta mapear estos pk en NIVEL_DJANGO_A_APP de ContentSyncRepository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
