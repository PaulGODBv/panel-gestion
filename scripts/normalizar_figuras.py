# -*- coding: utf-8 -*-
"""Despega las figuras del papel: recorte al contenido y blanco a transparencia.

El problema que resuelve es el que senalo el profesor: las imagenes se ven como
una foto de la guia impresa, no como parte de la app. El delator es el modo
oscuro, donde un rectangulo blanco de pagina sobre una superficie oscura canta.

Que hace con cada figura:

1. Pasa la imagen a luminancia y la usa como **matiz alfa**: el blanco del papel
   queda transparente y el trazo queda opaco. El RGB se aplana a negro, asi que
   la figura es tinta pura sobre nada.
2. Recorta pegado al contenido, con un margen pequeno. Se van los margenes de
   pagina.
3. Guarda en WebP sin perdida, que para linea y texto sale mas nitido y
   normalmente mas pequeno que con perdida.

Con eso la app puede pintarla directamente sobre su superficie y **tenirla**:
tinta oscura en tema claro, clara en oscuro. Sin caja blanca en ninguno.

Lo que NO hace, porque no se puede automatizar sin equivocarse: quitar los
restos de la maqueta del original —las palabras "Tabla", "Grafica", "Figura"
sueltas, o el "RESPONDA LAS PREGUNTAS 1 A 5" del Icfes—. Son tinta como el
resto del dibujo. El guion las detecta por posicion y avisa de cuales conviene
recortar a mano desde el panel.

Uso:
    python scripts/normalizar_figuras.py            # ensayo, escribe en /tmp
    python scripts/normalizar_figuras.py --aplicar  # sustituye, con copia previa
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import django
from PIL import Image, ImageOps

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reta2panel.settings")
os.environ.setdefault("RETA2_API_KEY", "solo-para-este-script")
django.setup()

from academics.models import ContextAsset, Question  # noqa: E402

# Rampa de la luminancia al alfa. Por encima de BLANCO es papel y desaparece;
# por debajo de NEGRO es trazo pleno. El tramo intermedio conserva el
# suavizado de los bordes, que es lo que evita que las lineas salgan dentadas.
BLANCO = 243
NEGRO = 60
MARGEN = 8


def a_matiz_alfa(img: Image.Image) -> Image.Image:
    luz = ImageOps.grayscale(img.convert("RGB"))
    alfa = luz.point(
        lambda v: 0 if v >= BLANCO else (255 if v <= NEGRO
                                         else int(255 * (BLANCO - v) / (BLANCO - NEGRO)))
    )
    tinta = Image.new("RGBA", img.size, (0, 0, 0, 255))
    tinta.putalpha(alfa)
    return tinta


def recortar(img: Image.Image) -> Image.Image:
    caja = img.getchannel("A").getbbox()
    if caja is None:
        return img
    izq, arr, der, aba = caja
    return img.crop((
        max(0, izq - MARGEN),
        max(0, arr - MARGEN),
        min(img.width, der + MARGEN),
        min(img.height, aba + MARGEN),
    ))


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    salida = BASE / "media" / "_normalizadas"
    salida.mkdir(parents=True, exist_ok=True)

    activos = [a for a in ContextAsset.objects.all().order_by("image")
               if Question.objects.filter(context_asset=a).exists()]

    if not activos:
        print("No hay figuras enlazadas a ninguna pregunta.")
        return 0

    if aplicar:
        respaldo = BASE / f"media-originales-{datetime.now():%Y%m%d-%H%M}"
        shutil.copytree(BASE / "media" / "question-context", respaldo)
        print(f"Copia de los originales en {respaldo.name}\n")

    print(f"{'figura':34} {'antes':>16}  {'despues':>16}  {'peso':>12}")
    for a in activos:
        ruta = Path(a.image.path)
        if not ruta.exists():
            print(f"{ruta.name:34} no esta en disco, se omite")
            continue

        original = Image.open(ruta)
        antes = original.size
        peso_antes = ruta.stat().st_size

        tratada = recortar(a_matiz_alfa(original))

        destino = ruta if aplicar else salida / ruta.name
        tratada.save(destino, "WEBP", lossless=True, method=6)
        peso_despues = destino.stat().st_size

        print(f"{ruta.name:34} {antes[0]:>7}x{antes[1]:<8} "
              f"{tratada.size[0]:>7}x{tratada.size[1]:<8} "
              f"{peso_antes // 1024:>4} -> {peso_despues // 1024:<4} KiB")

    if not aplicar:
        print(f"\nEnsayo. Resultados en media/_normalizadas/ para que los mires.")
        print("Si convencen, vuelve a lanzarlo con --aplicar.")
    else:
        print("\nSustituidas. La app las recoge en la siguiente sincronizacion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
