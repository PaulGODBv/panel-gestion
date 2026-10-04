# -*- coding: utf-8 -*-
"""Devuelve a `reading_text` el texto de huecos de "Greek and Roman cultures".

Segundo caso de prosa guardada como imagen, despues del de Oneida. Este no
tenia respuestas regaladas —el `reading_text` era solo la instruccion, y cada
pregunta reescribe su propia frase—, pero el texto seguia encerrado en
`geek_and_roman_culture.webp`: no se puede ampliar, no lo lee un lector de
pantalla y no sale en "Ver texto completo".

Se pierde la ilustracion del Coliseo, que era decorativa.

Uso:
    python scripts/reparar_texto_griegos_romanos.py            # ensayo
    python scripts/reparar_texto_griegos_romanos.py --aplicar  # escribe, con copia
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

# Transcrito de geek_and_roman_culture.webp. Los huecos se conservan con su
# numero: son los que reescribe cada pregunta.
PASAJE = """GREEK AND ROMAN CULTURES

The Greek culture, together with the Roman one, (0) _______ fascinated humans for centuries. Sadly, many people today (11) ___________ know the differences between Greeks and Romans.

Some people think Romans are an extension of Greeks; others assume that the two are similar. In fact, the two are very different (12) ___________ one another, and show opposite life values.

(13) _________ Greeks and Romans were great architects. Greeks used to (14) _________ more about shape than function. They (15) ___________ the most important thing was making beautiful buildings. (16) _________, Romans were perfect engineers. For (17) _______, street planning and use had the greatest importance.

Greeks admired poets and philosophers, (18) ___________ Romans admired their soldiers who were extremely brave and successful."""

IDS = [37, 38, 39, 40, 41, 90, 91, 92]


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    preguntas = list(Question.objects.filter(id__in=IDS).order_by("id"))

    if len(preguntas) != len(IDS):
        faltan = set(IDS) - {q.id for q in preguntas}
        print(f"No estan estas preguntas: {sorted(faltan)}. Se aborta.")
        return 1

    print(f"Pasaje nuevo: {len(PASAJE)} caracteres\n")
    for q in preguntas:
        imagen = q.context_asset.image.name.split("/")[-1] if q.context_asset else "-"
        print(f"  id{q.id}  reading_text {len(q.reading_text or ''):4} -> {len(PASAJE)}   imagen {imagen} -> -")

    if not aplicar:
        print("\nEnsayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    respaldo = BASE / f"db-antes-griegos-{datetime.now():%Y%m%d-%H%M}.sqlite3"
    shutil.copy2(BASE / "db.sqlite3", respaldo)
    print(f"\nCopia de seguridad: {respaldo.name}")

    for q in preguntas:
        q.reading_text = PASAJE
        q.context_asset = None
        q.save(update_fields=["reading_text", "context_asset", "updated_at"])

    print(f"{len(preguntas)} preguntas corregidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
