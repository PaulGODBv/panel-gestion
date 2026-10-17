# -*- coding: utf-8 -*-
"""Devuelve a `q100` su pasaje, y corrige la version corta que se invento.

EL FALLO. La pregunta «Segun la informacion presentada, la afirmacion del
funcionario podria tener como consecuencia que:» tenia como contexto el pasaje
del FMI y la analista economica —copiado de `q60`—, que no habla de ninguna
afirmacion de ningun funcionario. Pregunta y pasaje no eran de la misma
pregunta, y sin el pasaje bueno el item no se puede responder: las cuatro
opciones hablan de un estudio que en ninguna parte se menciona.

No fue la siembra: `CompetencyData.kt` ya lo traia asi, y todas las versiones
del historial de la app tambien. Nacio roto.

DE DONDE SALE EL PASAJE. Del cuadernillo oficial del ICFES, «Modulo de
Competencias ciudadanas - Cuadernillo de preguntas - Saber Pro 2018»,
icfes.gov.co, consultado el 16/10/2026. Es el item cuyas opciones coinciden
palabra por palabra con las que ya estaban en el banco, asi que no hay duda de
que es este y no otro.

Y LA VERSION CORTA TAMBIEN ESTABA MAL. El calentamiento que se cargo el
15/10 llevaba un contexto RECONSTRUIDO —una mujer que «se expuso» al salir
sola de noche— deducido de las opciones cuando el original no aparecia. La
idea que medía era la correcta, pero la escena no es esa: en la pregunta de
verdad el funcionario no habla de una victima concreta, sino que desacredita
un estudio y pide tener en cuenta «la justificacion de los hechos». Se
sustituye por un resumen fiel del pasaje real.

Uso:
    python scripts/reparar_pasaje_violencia.py            # ensayo
    python scripts/reparar_pasaje_violencia.py --aplicar  # escribe, con copia
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

from django.db import transaction  # noqa: E402

from academics.models import Question  # noqa: E402

# El pasaje del cuadernillo del ICFES, con sus tildes restituidas: la
# extraccion del PDF las pierde, pero el texto es el mismo.
PASAJE = (
    "Un estudio reveló que el 30 % de las mujeres en Colombia son víctimas de "
    "violencia física. A partir de este estudio varias organizaciones "
    "feministas solicitaron el endurecimiento de las penas para las personas "
    "que ejercían violencia contra las mujeres.\n\n"
    "Ante esta petición un funcionario del Gobierno señaló que el estudio no "
    "era confiable, porque no consideraba los distintos contextos de estas "
    "agresiones y que era muy importante tener en cuenta la justificación de "
    "los hechos."
)

# Como se reconoce cada una: por su enunciado, que es lo unico estable.
ENUNCIADO_LARGA = (
    "Según la información presentada, la afirmación del funcionario podría "
    "tener como consecuencia que:"
)
ENUNCIADO_CORTA_VIEJA = (
    "Ante un caso de violencia contra una mujer, un funcionario declara que "
    "ella «se expuso» al salir sola de noche. Esa afirmación puede llevar a que:"
)

# La corta, rehecha sobre el pasaje de verdad. Mismo criterio que las otras
# quince: se acorta la redaccion, no la discriminacion, y la correcta se
# queda donde estaba.
ENUNCIADO_CORTA_NUEVA = (
    "Un estudio dice que el 30 % de las mujeres en Colombia sufre violencia "
    "física. Un funcionario responde que no es confiable y que hay que ver la "
    "justificación de los hechos. Eso puede llevar a que:"
)


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    cambios = []

    larga = Question.objects.filter(text=ENUNCIADO_LARGA).first()
    if larga is None:
        print("No se encuentra la pregunta larga. Se aborta.")
        return 1

    if larga.reading_text == PASAJE:
        print(f"  pk={larga.id}: ya tiene el pasaje bueno, se omite")
    else:
        print(f"  pk={larga.id} (nivel {larga.level.name}): se le pone su pasaje")
        print(f"      tenia {len(larga.reading_text or '')} caracteres "
              f"—{(larga.reading_text or '')[:58]}…—")
        print(f"      pasa a {len(PASAJE)} caracteres")
        cambios.append(("pasaje", larga))

    corta = Question.objects.filter(text=ENUNCIADO_CORTA_VIEJA).first()
    if corta is None:
        print("  la version corta inventada ya no esta, se omite")
    else:
        print(f"  pk={corta.id} (nivel {corta.level.name}): se corrige el enunciado")
        print(f"      el contexto reconstruido no era la escena de la pregunta")
        cambios.append(("enunciado", corta))

    if not cambios:
        print("\nNada que hacer.")
        return 0

    if not aplicar:
        print("\nEnsayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    base_sqlite = BASE / "db.sqlite3"
    if base_sqlite.is_file():
        respaldo = BASE / f"db-antes-pasaje-{datetime.now():%Y%m%d-%H%M}.sqlite3"
        shutil.copy2(base_sqlite, respaldo)
        print(f"\nCopia de seguridad: {respaldo.name}")
    else:
        print("\nAVISO: no hay db.sqlite3, asi que NO se ha hecho copia.")
        print("Si esto corre contra PostgreSQL, respalda antes por tu cuenta.")

    with transaction.atomic():
        for que, pregunta in cambios:
            if que == "pasaje":
                pregunta.reading_text = PASAJE
                pregunta.save(update_fields=["reading_text"])
            else:
                pregunta.text = ENUNCIADO_CORTA_NUEVA
                pregunta.save(update_fields=["text"])

    print(f"\nArregladas {len(cambios)}.")
    print("\nFalta lo mismo en el catalogo empotrado de la app:")
    print("  CompetencyData.kt, pregunta id = 1015, su readingText.")
    print("  Solo importa sin conexion —con red el catalogo baja del panel—,")
    print("  pero el registro ocurre y se juega sin datos mas de lo que parece.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
