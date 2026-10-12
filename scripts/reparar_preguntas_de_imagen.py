# -*- coding: utf-8 -*-
"""Pone las dos imagenes que faltaban y corrige dos respuestas equivocadas.

Las cuatro preguntas con imagen del cuadernillo de Lectura Critica estaban en el
banco **sin ninguna imagen**, y en su lugar llevaban una descripcion escrita. La
vineta de Mafalda ya se arreglo aparte; aqui van las otras dos imagenes y las
dos respuestas que no coinciden con la tabla del Icfes.

LAS RESPUESTAS
--------------
La tabla del cuadernillo da, para las preguntas de la pagina 10, B y B; y para
las tres de la pagina 17, D, C y B.

Que numero es cada pregunta se dedujo del texto extraido, donde la etiqueta del
numero aparece **despues** de su bloque. Esa lectura se valido contra dos
preguntas de esa misma pagina que ya estan en el banco con la respuesta
correcta: `q70` sale C y `q72` sale D, y las dos cuadran. La lectura contraria
no cuadraba con ninguna.

  - q64: el banco dice A, es **B**. Las dos de Tetra Pak son B en la tabla, asi
    que esta no depende de acertar cual es la 10 y cual la 11.
  - q71: el banco dice A, es **B**. A no estaba ni entre las tres posibles.

LAS IMAGENES
------------
Las dos entran con `es_figura=False`. El anuncio de Tetra Pak es una
**fotografia** y la propaganda tambien: pasarlas por el matte de luminancia las
dejaria en negativo, igual que habria pasado con la vineta.

    python scripts/reparar_preguntas_de_imagen.py <tetrapak.png> <propaganda.png>
    python scripts/reparar_preguntas_de_imagen.py <tetrapak.png> <propaganda.png> --aplicar
"""
import os
import pathlib
import shutil
import sys
from datetime import datetime

import django

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.chdir(RAIZ)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reta2panel.settings")
django.setup()

from django.core.files.base import ContentFile  # noqa: E402

from academics.models import ContextAsset, Question  # noqa: E402

TETRA_ALT = ("Anuncio de Tetra Pak: un hombre empuja un carrito de supermercado "
             "con una vaca dentro, en un pasillo lleno de envases de leche.")
PROPA_ALT = ("Propaganda de una entidad financiera: una pareja sonriente mira "
             "algo juntos, bajo el lema «Escoge la madre de tus hijos».")
CREDITO = "Tomado del cuadernillo de preguntas de Lectura Critica, Icfes."

# pregunta -> opcion correcta nueva (1..4)
RESPUESTAS = {64: 2, 71: 2}


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    rutas = [pathlib.Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    if len(rutas) != 2:
        print("Hacen falta dos imagenes: la de Tetra Pak y la de la propaganda.")
        return 1
    tetra, propa = rutas
    for r in rutas:
        if not r.exists():
            print(f"No encuentro {r}")
            return 1

    print("IMAGENES (las dos con es_figura=False: son fotografias)")
    print(f"  Tetra Pak  {tetra.name:28} -> q63 y q64")
    print(f"  Propaganda {propa.name:28} -> q71")
    print()
    print("RESPUESTAS")
    for qid, nueva in RESPUESTAS.items():
        q = Question.objects.get(pk=qid)
        opciones = list(q.options.order_by("order", "id"))
        antes = q.correct_option_order
        print(f"  q{qid}: {'ABCD'[antes - 1]} -> {'ABCD'[nueva - 1]}")
        print(f"      antes: {opciones[antes - 1].text[:78]}")
        print(f"      ahora: {opciones[nueva - 1].text[:78]}")
    print()
    print("Y se vacia el pasaje de q71: describia la propaganda apuntando a la")
    print("opcion A, que es justo la que estaba mal. Con la imagen puesta sobra.")

    if not aplicar:
        print()
        print("ENSAYO: no se ha escrito nada. Repite con --aplicar.")
        return 0

    copia = RAIZ / f"db-antes-imagenes-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    shutil.copy2(RAIZ / "db.sqlite3", copia)
    print()
    print(f"Copia de la base en {copia.name}")

    recurso_tetra = ContextAsset(alt_text=TETRA_ALT, caption=CREDITO, es_figura=False)
    recurso_tetra.image.save(tetra.name, ContentFile(tetra.read_bytes()), save=True)
    Question.objects.filter(pk__in=[63, 64]).update(context_asset=recurso_tetra)
    print(f"Tetra Pak: imagen {recurso_tetra.pk} enlazada a q63 y q64")

    recurso_propa = ContextAsset(alt_text=PROPA_ALT, caption=CREDITO, es_figura=False)
    recurso_propa.image.save(propa.name, ContentFile(propa.read_bytes()), save=True)
    q71 = Question.objects.get(pk=71)
    q71.context_asset = recurso_propa
    q71.reading_text = ""
    q71.save(update_fields=["context_asset", "reading_text", "updated_at"])
    print(f"Propaganda: imagen {recurso_propa.pk} enlazada a q71, pasaje vaciado")

    for qid, nueva in RESPUESTAS.items():
        q = Question.objects.get(pk=qid)
        q.correct_option_order = nueva
        q.save(update_fields=["correct_option_order", "updated_at"])
        print(f"q{qid}: correcta = opcion {nueva}")

    return 0


sys.exit(main())
