"""Lleva el banco de CompetencyData.kt al panel, que es el paso 0 de TODO-1.

CompetencyData tiene los enunciados originales; el panel tiene una copia
parcial y con parte de la redaccion editada. Este script deja el panel igual
al original: crea las que faltan y corrige las que se desviaron.

No usa el importador CSV del panel a proposito: ese formato no lleva
`explanation` —la tienen las 94— ni `context_image` —la tienen 38—, asi que
importar por ahi perderia ambas cosas.

Por defecto NO escribe: imprime lo que haria. Con --aplicar, escribe.
"""
import argparse
import difflib
import os
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, r"C:\Users\Paul Mateo C\Documents\Proyect\panel-gestion")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reta2panel.settings")

import django

django.setup()

from django.db import transaction

from academics.models import Question, QuestionOption

KT = pathlib.Path(
    r"C:\Users\Paul Mateo C\AndroidStudioProjects\Reta2"
    r"\app\src\main\java\com\universidad\reta2\data\source\CompetencyData.kt"
)

ANDROID_A_DJANGO = {
    101: 1, 102: 2, 103: 3,
    201: 4, 202: 5, 203: 6,
    301: 7, 302: 8, 303: 9, 304: 10,
    401: 11, 402: 12, 403: 13,
}

CADENA = r'"((?:[^"\\]|\\.)*)"'
RE_OPCION = re.compile(r"QuestionOption\(\s*id\s*=\s*(\d+)\s*,\s*text\s*=\s*" + CADENA)


def desescapar(s):
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\W+", " ", s).strip().lower()


def campo(cuerpo, nombre):
    m = re.search(r"\b" + nombre + r"\s*=\s*" + CADENA, cuerpo)
    return desescapar(m.group(1)) if m else ""


def leer_kotlin():
    """{id_android: [pregunta, ...]} con todos los campos."""
    kt = KT.read_text(encoding="utf-8")
    marcas = [(int(m.group(1)), m.start()) for m in re.finditer(r"^\s{12}(\d{3}) ->", kt, re.M)]
    fuera = {}
    for i, (nivel, ini) in enumerate(marcas):
        fin = marcas[i + 1][1] if i + 1 < len(marcas) else len(kt)
        bloque = kt[ini:fin]
        preguntas = []
        # Cada Question empieza en "Question(" y termina donde empieza la siguiente.
        trozos = re.split(r"\n\s{16}Question\(", bloque)[1:]
        for cuerpo in trozos:
            m_texto = re.search(r"^\s*id\s*=\s*\d+,\s*\n\s*text\s*=\s*" + CADENA, cuerpo)
            if not m_texto:
                continue
            opciones = [(int(i_), desescapar(t)) for i_, t in RE_OPCION.findall(cuerpo)]
            m_correcta = re.search(r"correctOptionId\s*=\s*(\d+)", cuerpo)
            if not (opciones and m_correcta):
                continue
            id_correcta = int(m_correcta.group(1))
            orden_correcta = next(
                (n for n, (oid, _) in enumerate(opciones, start=1) if oid == id_correcta), 1
            )
            preguntas.append({
                "text": desescapar(m_texto.group(1)),
                "options": [t for _, t in opciones],
                "correct_order": orden_correcta,
                "explanation": campo(cuerpo, "explanation"),
                "reading_text": campo(cuerpo, "readingText"),
                "context_image": campo(cuerpo, "contextImage"),
            })
        fuera[nivel] = preguntas
    return fuera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true", help="escribe en la base")
    args = ap.parse_args()

    banco = leer_kotlin()
    crear, actualizar, sin_tocar, sobrantes = [], [], 0, []

    for and_id, dj_id in ANDROID_A_DJANGO.items():
        originales = banco.get(and_id, [])
        existentes = list(Question.objects.filter(level_id=dj_id))
        libres = {q.id: norm(q.text) for q in existentes}
        usadas = set()

        for p in originales:
            n = norm(p["text"])
            pareja = next((qid for qid, qn in libres.items() if qn == n and qid not in usadas), None)
            if pareja is None:
                candidatas = {qid: qn for qid, qn in libres.items() if qid not in usadas}
                cerca = difflib.get_close_matches(n, list(candidatas.values()), n=1, cutoff=0.55)
                if cerca:
                    pareja = next(qid for qid, qn in candidatas.items() if qn == cerca[0])
            if pareja is None:
                crear.append((dj_id, p))
            else:
                usadas.add(pareja)
                q = next(x for x in existentes if x.id == pareja)
                if norm(q.text) == n and (q.explanation or "") == p["explanation"]:
                    sin_tocar += 1
                else:
                    actualizar.append((q, p))

        for q in existentes:
            if q.id not in usadas:
                sobrantes.append(q)

    print(f"preguntas originales en CompetencyData : {sum(len(v) for v in banco.values())}")
    print(f"preguntas hoy en el panel              : {Question.objects.count()}")
    print()
    print(f"  se crearian                          : {len(crear)}")
    print(f"  se corregirian (redaccion/explicacion): {len(actualizar)}")
    print(f"  ya coinciden                         : {sin_tocar}")
    print(f"  quedan en el panel sin pareja        : {len(sobrantes)}")
    print()
    con_imagen = sum(1 for _, p in crear if p["context_image"])
    print(f"  de las nuevas, con imagen de contexto: {con_imagen}")
    print()
    for q in sobrantes:
        print(f"   sin pareja | nivel {q.level_id} | {q.text[:70]}")

    if not args.aplicar:
        print()
        print("DRY RUN: no se ha escrito nada. Añade --aplicar para ejecutar.")
        return

    with transaction.atomic():
        for dj_id, p in crear:
            q = Question.objects.create(
                level_id=dj_id,
                text=p["text"],
                reading_text=p["reading_text"],
                explanation=p["explanation"],
                context_image=p["context_image"],
                correct_option_order=p["correct_order"],
            )
            for n, t in enumerate(p["options"], start=1):
                QuestionOption.objects.create(question=q, text=t, order=n)

        for q, p in actualizar:
            q.text = p["text"]
            q.reading_text = p["reading_text"]
            q.explanation = p["explanation"]
            q.context_image = p["context_image"]
            q.correct_option_order = p["correct_order"]
            q.save()
            q.options.all().delete()
            for n, t in enumerate(p["options"], start=1):
                QuestionOption.objects.create(question=q, text=t, order=n)

    print()
    print(f"APLICADO. Panel: {Question.objects.count()} preguntas.")


if __name__ == "__main__":
    main()
