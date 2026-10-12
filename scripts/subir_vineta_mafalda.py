# -*- coding: utf-8 -*-
"""Sube la vineta de Mafalda y la enlaza a la pregunta que la necesita.

La pregunta q69 —«Mafalda le da a la tortuga el nombre Burocracia con el
proposito de destacar que la burocracia es...»— esta en el banco **sin su
imagen**, y sin la vineta no se puede responder. En su lugar alguien escribio
una descripcion que ademas **regala la respuesta**:

    «...destacar que la burocracia es lenta y CAPRICHOSA en su comportamiento»

y la opcion correcta es «caprichosa en la organizacion de los horarios». Este
guion pone la imagen y quita esa descripcion.

La vineta se sube con `es_figura=False`, que es lo que impide el matte de
luminancia. Con el matte puesto la historieta sale **en negativo**: el blanco de
los bocadillos y de las caras se vuelve transparente y lo que queda es la tinta,
asi que Mafalda pasa a ser una mancha. En una figura de linea —una tabla, una
grafica— quitar el papel es justo lo que se quiere; en una historieta el blanco
significa algo.

Procedencia: cuadernillo de preguntas de Lectura Critica del Icfes, modulo de
lectura critica. La tira es de Quino, reproducida por el Icfes.

    python scripts/subir_vineta_mafalda.py            # ensayo, no escribe
    python scripts/subir_vineta_mafalda.py --aplicar  # escribe, con copia
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

ID_PREGUNTA = 69
ALT = ("Tira de Mafalda: una amiga visita a la tortuga llamada Burocracia y no "
       "logra verla porque siempre esta cerrada o el horario es incierto.")
LEYENDA = "Quino. Tomado del cuadernillo de preguntas de Lectura Critica, Icfes."


def main() -> int:
    aplicar = "--aplicar" in sys.argv

    origen = None
    for candidata in sys.argv[1:]:
        if not candidata.startswith("--"):
            origen = pathlib.Path(candidata)
    if origen is None:
        print("Falta la ruta de la imagen.")
        print("  python scripts/subir_vineta_mafalda.py <imagen.png> [--aplicar]")
        return 1
    if not origen.exists():
        print(f"No encuentro la imagen: {origen}")
        return 1

    try:
        pregunta = Question.objects.get(pk=ID_PREGUNTA)
    except Question.DoesNotExist:
        print(f"No existe la pregunta {ID_PREGUNTA}.")
        return 1

    print(f"Pregunta {pregunta.pk} (nivel {pregunta.level_id})")
    print(f"  enunciado : {pregunta.text[:92]}")
    print(f"  imagen hoy: {pregunta.context_asset or '(ninguna)'}")
    print(f"  pasaje hoy: {(pregunta.reading_text or '(vacio)')[:140]}")
    print()
    print(f"Imagen a subir: {origen.name}  ({origen.stat().st_size // 1024} KiB)")
    print("  es_figura = False  -> sin matte: la vineta entra tal cual")
    print()
    print("Cambios:")
    print("  1. Alta de la imagen de contexto y enlace a la pregunta.")
    print("  2. Vaciado del pasaje, que describia la vineta Y REGALABA LA RESPUESTA.")
    print("     La imagen se basta sola; el enunciado ya dice lo que hay que mirar.")

    if not aplicar:
        print()
        print("ENSAYO: no se ha escrito nada. Repite con --aplicar.")
        return 0

    copia = RAIZ / f"db-antes-mafalda-{datetime.now():%Y%m%d-%H%M%S}.sqlite3"
    shutil.copy2(RAIZ / "db.sqlite3", copia)
    print()
    print(f"Copia de la base en {copia.name}")

    recurso = ContextAsset(alt_text=ALT, caption=LEYENDA, es_figura=False)
    recurso.image.save(origen.name, ContentFile(origen.read_bytes()), save=True)

    pregunta.context_asset = recurso
    pregunta.reading_text = ""
    pregunta.save(update_fields=["context_asset", "reading_text", "updated_at"])

    recurso.refresh_from_db()
    print(f"Imagen {recurso.pk} guardada como {recurso.image.name}")
    print(f"  es_figura = {recurso.es_figura}")
    print(f"Pregunta {pregunta.pk} enlazada, pasaje vaciado.")
    return 0


sys.exit(main())
