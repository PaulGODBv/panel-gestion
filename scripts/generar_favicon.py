"""Genera el icono de pestana a partir del escudo, sin recortarlo.

Se corre desde la raiz del proyecto:  python scripts/generar_favicon.py

Vive aqui y no junto al icono porque todo lo que esta bajo `static/` lo
recoge `collectstatic` y lo sirve WhiteNoise: un .py ahi dentro acabaria
publicado.

Se eligio el escudo entero —trazado A de los tres— a sabiendas de que los dos
anillos de texto no se leen a 16 px. La fidelidad al escudo institucional pesa
mas que la legibilidad de un texto que, a ese tamano, no iba a leerse de
ninguna forma.

El fondo se fija en blanco en vez de dejar la transparencia del PNG original:
el escudo es azul oscuro, y sobre la barra de pestanas en modo oscuro se
quedaria practicamente invisible.
"""
from PIL import Image

ORIGEN = "static/landing/img/escudo-udes.png"
DESTINO = "static/marca"

base = Image.open(ORIGEN).convert("RGBA")

# Cuadrar sin estirar: el escudo es 119x120 y un icono es cuadrado.
lado = max(base.size)
lienzo = Image.new("RGBA", (lado, lado), (255, 255, 255, 255))
lienzo.paste(base, ((lado - base.size[0]) // 2, (lado - base.size[1]) // 2), base)
escudo = lienzo.convert("RGB")

# El .ico lleva las tres medidas dentro: el navegador escoge la que necesita.
# Con una sola, el reescalado lo hace el navegador y sale peor.
escudo.save(f"{DESTINO}/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

escudo.resize((32, 32), Image.LANCZOS).save(f"{DESTINO}/favicon-32.png")
escudo.resize((180, 180), Image.LANCZOS).save(f"{DESTINO}/apple-touch-icon.png")

import os
for f in sorted(os.listdir(DESTINO)):
    print(f"  {f:24} {os.path.getsize(os.path.join(DESTINO, f)):>7} bytes")
