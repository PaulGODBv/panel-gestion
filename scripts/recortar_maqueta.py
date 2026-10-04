# -*- coding: utf-8 -*-
"""Quita de una figura la franja superior que era maqueta del original.

`normalizar_figuras.py` despega la figura del papel, pero no puede distinguir el
dibujo de los restos de la guia impresa: para el son tinta igual. Algunos de
esos restos no solo sobran, sino que **dicen algo falso dentro de la app**. El
caso claro es `imagen_sismos`, que arrastra el encabezado del Icfes «RESPONDA
LAS PREGUNTAS 1 A 5 DE ACUERDO CON LA SIGUIENTE INFORMACION»: en la app no hay
preguntas numeradas del 1 al 5, y el estudiante lee una instruccion que no se
corresponde con lo que tiene delante.

El corte se hace por la primera franja horizontal sin tinta, que es la
separacion natural entre el encabezado y el contenido.

**Mira siempre el ensayo antes de aplicar.** El guion no sabe distinguir un
encabezado sobrante del titulo de la propia figura: en `imagen_jabones` esa
primera franja separa el titulo «Precios por unidad de diferentes
presentaciones...» del resto, y recortarlo destruiria la tabla. De las diez
figuras del banco, la unica que lo necesitaba era `imagen_sismos`.

Uso:
    python scripts/recortar_maqueta.py <archivo.webp>            # ensayo
    python scripts/recortar_maqueta.py <archivo.webp> --aplicar
"""
import shutil
import sys
from pathlib import Path

from PIL import Image

BASE = Path(__file__).resolve().parent.parent
FIGURAS = BASE / "media" / "question-context"
ALTO_MINIMO_DE_FRANJA = 10
UMBRAL_DE_TINTA = 12


def primera_franja_en_blanco(alfa: Image.Image):
    """(inicio, fin) de la primera franja sin tinta, o None."""
    ancho, alto = alfa.size
    inicio = None
    for y in range(alto):
        hay_tinta = alfa.crop((0, y, ancho, y + 1)).getextrema()[1] >= UMBRAL_DE_TINTA
        if not hay_tinta and inicio is None:
            inicio = y
        elif hay_tinta and inicio is not None:
            if y - inicio >= ALTO_MINIMO_DE_FRANJA:
                return inicio, y
            inicio = None
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    ruta = FIGURAS / sys.argv[1]
    aplicar = "--aplicar" in sys.argv

    if not ruta.exists():
        print(f"No existe {ruta}")
        return 1

    img = Image.open(ruta).convert("RGBA")
    franja = primera_franja_en_blanco(img.getchannel("A"))

    if franja is None:
        print(f"{ruta.name}: no hay franja en blanco; nada que recortar.")
        return 0

    inicio, fin = franja
    if inicio > img.height * 0.25:
        print(f"{ruta.name}: la primera franja empieza en y={inicio} de {img.height}, "
              "demasiado abajo para ser un encabezado. No se toca.")
        return 0

    print(f"{ruta.name}: {img.width}x{img.height} -> {img.width}x{img.height - fin} "
          f"(se van las {fin} primeras filas)")

    if not aplicar:
        print("Ensayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    respaldo = ruta.with_suffix(".webp.antes-del-recorte")
    shutil.copy2(ruta, respaldo)
    img.crop((0, fin, img.width, img.height)).save(ruta, "WEBP", lossless=True, method=6)
    print(f"Recortada. Original en {respaldo.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
