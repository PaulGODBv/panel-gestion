"""Convierte las imagenes de contexto de nombres de drawable en archivos reales.

Hasta ahora `Question.context_image` guardaba un nombre como "imagen_sismos" y
la app lo resolvia con getIdentifier() contra los drawables del APK. Eso obliga
a recompilar la app cada vez que se anade una imagen.

Este script sube los PNG que hoy viven en el repo de Android a MEDIA_ROOT, crea
un ContextAsset por cada uno y enlaza las preguntas que lo usaban. El texto
alternativo sale de los comentarios que acompanan a cada `contextImage` en
CompetencyData.kt, que describen lo que se ve.

Por defecto NO escribe. Con --aplicar, escribe.
"""
import argparse
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reta2panel.settings")

import django

django.setup()

from django.core.files import File
from django.db import transaction

from academics.models import ContextAsset, Question

ANDROID = pathlib.Path(r"C:\Users\Paul Mateo C\AndroidStudioProjects\Reta2")
DRAWABLE = ANDROID / "app" / "src" / "main" / "res" / "drawable"
KT = ANDROID / "app" / "src" / "main" / "java" / "com" / "universidad" / "reta2" / "data" / "source" / "CompetencyData.kt"

RE_CON_COMENTARIO = re.compile(r'contextImage\s*=\s*"([^"]+)"\s*//\s*(.+)')
RE_NOMBRE = re.compile(r'contextImage\s*=\s*"([^"]+)"')


def descripciones():
    """{nombre_drawable: texto alternativo} sacado de los comentarios del Kotlin."""
    kt = KT.read_text(encoding="utf-8")
    fuera = {n: "" for n in RE_NOMBRE.findall(kt)}
    for nombre, comentario in RE_CON_COMENTARIO.findall(kt):
        fuera[nombre] = comentario.strip()
    return fuera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    alt = descripciones()
    usados = sorted(
        n for n in Question.objects.exclude(context_image="")
        .values_list("context_image", flat=True).distinct()
    )

    plan, sin_archivo, sin_alt = [], [], []
    for nombre in usados:
        archivo = DRAWABLE / f"{nombre}.png"
        if not archivo.exists():
            sin_archivo.append(nombre)
            continue
        texto = alt.get(nombre, "")
        if not texto:
            texto = nombre.replace("_", " ").capitalize()
            sin_alt.append(nombre)
        cuantas = Question.objects.filter(context_image=nombre).count()
        plan.append((nombre, archivo, texto, cuantas))

    print(f"nombres de imagen en uso : {len(usados)}")
    print(f"con archivo PNG en el repo: {len(plan)}")
    if sin_archivo:
        print(f"SIN ARCHIVO (se omiten)   : {', '.join(sin_archivo)}")
    print()
    for nombre, archivo, texto, cuantas in plan:
        kb = archivo.stat().st_size // 1024
        print(f"  {nombre:24s} {kb:4d} KB  x{cuantas:2d} preguntas  | {texto}")
    if sin_alt:
        print()
        print("Sin comentario en el Kotlin, el texto alternativo sale del nombre")
        print("y conviene revisarlo a mano: " + ", ".join(sin_alt))

    if not args.aplicar:
        print()
        print("DRY RUN: no se ha escrito nada. Anade --aplicar para ejecutar.")
        return

    creados = enlazadas = 0
    with transaction.atomic():
        for nombre, archivo, texto, _ in plan:
            activo = ContextAsset.objects.filter(alt_text=texto).first()
            if activo is None:
                activo = ContextAsset(alt_text=texto)
                with archivo.open("rb") as fh:
                    activo.image.save(f"{nombre}.png", File(fh), save=True)
                creados += 1
            enlazadas += Question.objects.filter(context_image=nombre).update(
                context_asset=activo
            )

    print()
    print(f"APLICADO. Imagenes creadas: {creados} | preguntas enlazadas: {enlazadas}")


if __name__ == "__main__":
    main()
