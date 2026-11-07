# -*- coding: utf-8 -*-
"""Deja un icono de nivel listo para que la app lo pinte igual que los demás.

POR QUÉ EXISTE. Los trece iconos que ya tiene la app se hicieron con el Image
Asset de Android Studio, que es la herramienta del **icono de lanzador**:
genera un `<adaptive-icon>` con capa de fondo y de frente, en cinco
densidades, diecisiete archivos por icono. Nada de eso hace falta aquí. En la
pantalla de niveles el icono se dibuja dentro de una caja de 48 dp que ya lo
recorta sola, así que lo que la app necesita es **un PNG cuadrado**.

Lo que sí hace falta, y es lo que hace este módulo, es que todos salgan
iguales. Un profesor sube lo que tenga a mano: un JPG de 1200×900 con fondo
blanco, o un PNG recortado al ras del dibujo. Puestos en columna sin tocar,
uno se ve enorme y el otro flotando. Aquí se les da a todos el mismo lado, el
mismo aire alrededor y el mismo formato.

No importa Django a propósito, igual que `importador` y `lector_pdf`: así se
puede ejecutar y probar solo.
"""
from __future__ import annotations

import io

from PIL import Image

#: Lado del PNG que se guarda.
#:
#: La app lo pinta a 48 dp. En una pantalla xxxhdpi eso son 192 px reales, así
#: que 256 da margen de sobra y deja que Coil reduzca, que siempre se ve mejor
#: que ampliar. Pesa unos pocos kilobytes, que es lo que permite guardarlo en
#: la base en vez de montar almacenamiento externo.
LADO = 256

#: Aire alrededor del dibujo, en proporción al lado.
#:
#: Sin esto, un icono recortado al ras toca los bordes y otro con márgenes
#: propios se ve pequeño al lado. Recortando al contenido y volviendo a dejar
#: SIEMPRE este margen, los dos acaban ocupando lo mismo.
MARGEN = 0.08

#: Lo más grande que se acepta de entrada, en bytes.
MAXIMO_DE_ENTRADA = 5 * 1024 * 1024


class IconoInvalido(Exception):
    """Lo que subieron no sirve, y el mensaje dice por qué."""


def normalizar(datos: bytes) -> bytes:
    """Un archivo de imagen cualquiera, convertido en el PNG que espera la app.

    Cuadrado, de [LADO] píxeles, con fondo transparente y el dibujo centrado
    dejando [MARGEN] de aire. Devuelve los bytes del PNG.
    """
    if not datos:
        raise IconoInvalido("El archivo está vacío.")
    if len(datos) > MAXIMO_DE_ENTRADA:
        megas = MAXIMO_DE_ENTRADA / 1024 / 1024
        raise IconoInvalido(f"La imagen pasa de {megas:.0f} MB.")

    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.load()
    except Exception as e:
        raise IconoInvalido(
            "No se pudo leer la imagen. Tiene que ser un PNG, un JPG o un WebP."
        ) from e

    imagen = imagen.convert("RGBA")

    # Un JPG no tiene transparencia: su fondo blanco llega como blanco opaco y
    # se vería como un cuadro detrás del dibujo. Se quita el blanco de las
    # esquinas antes de recortar; si la imagen ya traía alfa, esto no la toca.
    if _parece_fondo_blanco(imagen):
        imagen = _blanco_a_transparente(imagen)

    # Al contenido primero: es lo que iguala a quien subió con márgenes y a
    # quien subió al ras.
    caja = imagen.getbbox()
    if caja is None:
        raise IconoInvalido("La imagen está en blanco: no se ve nada en ella.")
    imagen = imagen.crop(caja)

    # Cuadrado por el lado mayor, sin deformar.
    dentro = int(LADO * (1 - 2 * MARGEN))
    imagen.thumbnail((dentro, dentro), Image.LANCZOS)

    lienzo = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    lienzo.paste(
        imagen,
        ((LADO - imagen.width) // 2, (LADO - imagen.height) // 2),
        imagen,
    )

    salida = io.BytesIO()
    lienzo.save(salida, format="PNG", optimize=True)
    return salida.getvalue()


def _parece_fondo_blanco(imagen: Image.Image) -> bool:
    """Las cuatro esquinas opacas y casi blancas."""
    w, h = imagen.size
    esquinas = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    for x, y in esquinas:
        r, g, b, a = imagen.getpixel((x, y))
        if a < 250 or min(r, g, b) < 240:
            return False
    return True


def _blanco_a_transparente(imagen: Image.Image) -> Image.Image:
    """El blanco se vuelve transparente, en proporción a lo blanco que sea.

    No es un umbral duro —«si es más claro que X, fuera»— porque eso deja los
    bordes del dibujo dentados. Se usa lo oscuro de cada píxel como opacidad,
    que conserva el antialiasing con el que venía.
    """
    pixeles = imagen.load()
    w, h = imagen.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixeles[x, y]
            if a == 0:
                continue
            claridad = min(r, g, b)
            pixeles[x, y] = (r, g, b, min(a, 255 - claridad))
    return imagen
