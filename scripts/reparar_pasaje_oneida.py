# -*- coding: utf-8 -*-
"""Devuelve el pasaje de Oneida a `reading_text` y retira la imagen que lo contenia.

El problema tenia dos caras y se arreglan juntas:

1. El pasaje de comprension lectora vivia dentro de `social_experiment_text.webp`.
   Una imagen no se puede ampliar, no la lee un lector de pantalla, no se puede
   acortar y no sale en el desplegable de "Ver texto completo".

2. Lo que habia en `reading_text` de las preguntas 42 a 46 no era el pasaje, sino
   un resumen que **contiene las respuestas**: «travelled to New York State to
   change his way of life», «now functions as a hotel», «They studied Latin and
   Greek»... Cada frase resuelve una pregunta. Las cinco eran regalables.

Las 93 y 94 no tenian `reading_text` ninguno, asi que dependian por completo de
la imagen.

Uso:
    python scripts/reparar_pasaje_oneida.py            # solo enseña que haria
    python scripts/reparar_pasaje_oneida.py --aplicar  # escribe, con copia previa
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

from academics.models import Question  # noqa: E402

# Transcrito de social_experiment_text.webp, que es donde estaba encerrado.
PASAJE = """A SOCIAL EXPERIMENT IN ONEIDA, NEW YORK

In the nineteenth century there was a village called Oneida in New York State where a "family" of 300 members lived together in a large beautiful house where they shared everything.

A man named John Humphrey Noyes, and a small group of people moved there in 1848. They wanted a place where they could live according to their particular beliefs in their efforts to create a more equal society.

Today, this place is touristic and, like me, many visitors come because they had relatives among those 19th century dreamers. Others just want to see for themselves the building where this successful social group in American history lived. "I don't know of anywhere else where you can live in a historical place," said the director of the Oneida site. "It's very unusual."

The present owners share the building with guests who stay in large comfortably furnished bedrooms with private baths. There are eight guest rooms in the hotel area, and each guest pays $100 for a big bedroom, a simple breakfast and a private tour of the 10,300-square-meter building, which also contains 35 apartments.

The library and the building's grounds are also open to guests, as well as several of the public rooms. The 170-year-old library, unchanged from the original construction, holds a rich collection of 19th century books and magazines, which learners used to study Latin, Greek, algebra and astronomy.

This place is open for everybody and it's worth a visit."""

IDS = [42, 43, 44, 45, 46, 93, 94]


def copia_de_seguridad() -> Path:
    origen = BASE / "db.sqlite3"
    destino = BASE / f"db-antes-oneida-{datetime.now():%Y%m%d-%H%M}.sqlite3"
    shutil.copy2(origen, destino)
    return destino


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    preguntas = list(Question.objects.filter(id__in=IDS).order_by("id"))

    if len(preguntas) != len(IDS):
        faltan = set(IDS) - {q.id for q in preguntas}
        print(f"No estan estas preguntas: {sorted(faltan)}. Se aborta.")
        return 1

    print(f"Pasaje nuevo: {len(PASAJE)} caracteres\n")
    for q in preguntas:
        antes = q.reading_text or ""
        imagen = q.context_asset.image.name.split("/")[-1] if q.context_asset else "—"
        print(f"  id{q.id}  reading_text {len(antes):4} -> {len(PASAJE)}   imagen {imagen} -> —")

    if not aplicar:
        print("\nEnsayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    respaldo = copia_de_seguridad()
    print(f"\nCopia de seguridad: {respaldo.name}")

    for q in preguntas:
        q.reading_text = PASAJE
        # La imagen era el propio texto: una vez que el texto esta donde debe,
        # dejarla enlazada solo duplicaria el pasaje en pantalla.
        q.context_asset = None
        q.save(update_fields=["reading_text", "context_asset", "updated_at"])

    print(f"{len(preguntas)} preguntas corregidas.")
    print("Hay que sincronizar la app para que le llegue: se hace sola en el arranque.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
