# -*- coding: utf-8 -*-
"""Devuelve a los textos de lectura del panel lo que les falta.

**La causa.** En `CompetencyData.kt` los pasajes largos se escriben concatenando
trozos con `+` a lo largo de muchas lineas. El guion que sembro el panel desde
ahi se quedo con **el primer trozo** de cada uno, asi que varios contextos
llegaron cortados a mitad de frase. No se noto entonces porque los cortos
—que caben en una sola linea— entraron enteros.

**Como se emparejan sin adivinar.** Lo que hay guardado en el panel es un
*prefijo exacto* del original, porque es literalmente su primer trozo. Asi que
se busca el pasaje de `CompetencyData` que empieza por el texto del panel. Si
hay uno solo y es mas largo, estaba truncado. Si hay varios candidatos —dos
pasajes que empiezan igual— se elige el mas corto de los que lo contienen, que
es el que menos supone; y si ni eso desempata, se deja y se avisa, porque
inventar cual era seria peor que dejarlo corto.

Uso:
    python scripts/reparar_contextos_truncados.py            # ensayo
    python scripts/reparar_contextos_truncados.py --aplicar  # escribe, con copia
"""
import os
import re
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

FUENTE = Path(
    r"C:\Users\Paul Mateo C\AndroidStudioProjects\Reta2"
    r"\app\src\main\java\com\universidad\reta2\data\source\CompetencyData.kt"
)

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "$": "$", "'": "'"}


def leer_literal(texto, i):
    """Lee un literal de Kotlin que empieza en `texto[i] == '"'`.

    Devuelve (contenido, indice justo despues de la comilla de cierre).
    Hace falta a mano porque una expresion regular no distingue una comilla
    de cierre de una escapada, y estos pasajes estan llenos de dialogos.
    """
    assert texto[i] == '"'
    i += 1
    trozos = []
    while i < len(texto):
        c = texto[i]
        if c == "\\":
            siguiente = texto[i + 1]
            if siguiente == "u":
                trozos.append(chr(int(texto[i + 2:i + 6], 16)))
                i += 6
            else:
                trozos.append(ESCAPES.get(siguiente, siguiente))
                i += 2
        elif c == '"':
            return "".join(trozos), i + 1
        else:
            trozos.append(c)
            i += 1
    raise ValueError("literal sin cerrar")


def pasajes_de_la_fuente():
    """Todos los `readingText` de CompetencyData, con sus trozos ya unidos."""
    texto = FUENTE.read_text(encoding="utf-8")
    encontrados = []

    for m in re.finditer(r"readingText\s*=\s*", texto):
        i = m.end()
        partes = []
        while True:
            while i < len(texto) and texto[i] in " \t\r\n":
                i += 1
            if i >= len(texto) or texto[i] != '"':
                break
            contenido, i = leer_literal(texto, i)
            partes.append(contenido)
            j = i
            while j < len(texto) and texto[j] in " \t\r\n":
                j += 1
            if j < len(texto) and texto[j] == "+":
                i = j + 1
            else:
                break
        if partes:
            encontrados.append("".join(partes))

    return encontrados


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    pasajes = pasajes_de_la_fuente()
    print(f"{len(pasajes)} pasajes leidos de CompetencyData\n")

    arreglables, ambiguos = [], []

    for q in Question.objects.exclude(reading_text="").order_by("id"):
        actual = q.reading_text
        candidatos = [p for p in pasajes if p.startswith(actual) and len(p) > len(actual)]
        if not candidatos:
            continue
        unicos = sorted(set(candidatos), key=len)
        if len(unicos) > 1 and unicos[0] != unicos[-1]:
            # Varios pasajes distintos empiezan igual: no se elige por sorteo.
            ambiguos.append((q, len(actual), [len(c) for c in unicos]))
            continue
        arreglables.append((q, actual, unicos[0]))

    if ambiguos:
        print("AMBIGUOS (varios originales empiezan igual, no se tocan):")
        for q, n, largos in ambiguos:
            print(f"  id{q.id}: {n} car, candidatos de {largos}")
        print()

    if not arreglables:
        print("No hay contextos truncados que reparar.")
        return 0

    print(f"{len(arreglables)} contextos truncados:\n")
    for q, actual, completo in arreglables:
        print(f"  id{q.id:3} nivel {q.level_id:2}  {len(actual):5} -> {len(completo):5} car")
        print(f"        termina en: ...{actual[-46:]!r}")

    if not aplicar:
        print("\nEnsayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    respaldo = BASE / f"db-antes-contextos-{datetime.now():%Y%m%d-%H%M}.sqlite3"
    shutil.copy2(BASE / "db.sqlite3", respaldo)
    print(f"\nCopia de seguridad: {respaldo.name}")

    for q, _, completo in arreglables:
        q.reading_text = completo
        q.save(update_fields=["reading_text", "updated_at"])

    print(f"{len(arreglables)} contextos completados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
