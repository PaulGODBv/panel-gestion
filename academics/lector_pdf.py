# -*- coding: utf-8 -*-
"""Convierte un PDF de preguntas en el texto que entiende el importador.

POR QUÉ EXISTE. Un profesor intentó cargar preguntas en una reunión y preguntó
si podía subir un PDF y que se leyera solo, como al subir uno a Microsoft
Forms. Tenía razón en preguntarlo: escribe las preguntas en el computador y
exportarlas ya es un paso que da.

QUÉ HACE Y QUÉ NO
-----------------
Saca el texto, parte en preguntas y opciones, y lo escribe en el formato de
`importador`. **No escribe nada en la base.** Lo que devuelve va al cuadro de
texto de la pantalla de importar, para que la persona lo lea, pulse Revisar y
corrija lo que haga falta. Esa pantalla es lo que hace seguro un lector
imperfecto: un fallo se ve antes de guardar, no después.

**No adivina cuál es la correcta.** Si el documento la marca de alguna forma
reconocible —un asterisco, «(correcta)», un «Respuesta: b»— la respeta. Si no,
deja todas las opciones sin marcar y se elige con un clic en la revisión.

LO QUE DEPENDE DE CÓMO SE HIZO EL PDF, no de lo que contiene:

* Generado por software —Word, Google Docs, ReportLab— sale limpio.
* Maquetado para imprenta, con fuentes recortadas, sale peor pero sale: el
  cuadernillo del ICFES da 31.000 caracteres legibles.
* Escaneado es una foto, y ahí no hay texto que leer. Haría falta OCR, que es
  otro problema.

Este módulo no importa Django a propósito, igual que `importador`: así se
puede ejecutar y probar solo.
"""
from __future__ import annotations

import logging
import re

#: Una pregunta empieza por «12.» o «12)», al principio o tras un espacio.
PREGUNTA = re.compile(r"(?:(?<=\s)|^)(\d{1,3})\s*[.)]\s+")

#: Cuanto texto tiene que haber delante del numero de pregunta para tratarlo
#: como contexto y no como ruido. Cuarenta caracteres es poco mas de una linea:
#: por debajo de eso suele ser un resto de la pagina —un numero de pagina, el
#: titulo de la seccion— y no vale la pena ensuciar el bloque con ello.
MINIMO_DE_CONTEXTO = 40

#: Una opción, por «a.» «b)» «A.» … Hasta la h: el banco tiene preguntas de
#: ocho opciones —las de unir parejas de «Feelings»—, y el importador las
#: admite.
OPCION = re.compile(r"(?:(?<=\s)|^)([a-hA-H])\s*[.)]\s+")

#: Cómo suele venir marcada la correcta en un documento que sí la trae.
MARCA_EN_LA_OPCION = re.compile(
    r"\s*(?:\*+|\(correcta\)|\[correcta\]|\(clave\)|✔|✓|<-{1,2}|←)\s*$",
    re.IGNORECASE,
)
RESPUESTA_SUELTA = re.compile(
    r"\s*(?:respuesta|clave|correcta)\s*:?\s*([a-hA-H])\s*[.)]?\s*$",
    re.IGNORECASE,
)
EXPLICACION = re.compile(
    r"\s*(?:explicaci[oó]n|justificaci[oó]n|porque)\s*:\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)
CONTEXTO = re.compile(
    r"^\s*(?:contexto|texto|lectura|pasaje)\s*:\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)

#: Lo que se descarta antes de buscar preguntas: encabezados, pies y números
#: de página sueltos, que en un PDF maquetado se cuelan entre el texto.
RUIDO = re.compile(r"^\s*(?:p[áa]gina\s+\d+|\d+\s*/\s*\d+|\d{1,3})\s*$", re.IGNORECASE)


class PdfIlegible(Exception):
    """El archivo no es un PDF, está cifrado, o no tiene texto que sacar."""


def texto_de(fichero) -> str:
    """El texto plano del PDF, página a página.

    `fichero` es cualquier cosa que pypdf acepte: una ruta o un archivo
    abierto en binario, que es lo que llega de un formulario.
    """
    try:
        from pypdf import PdfReader
    except ImportError as e:  # pragma: no cover - solo si falta la dependencia
        raise PdfIlegible(
            "Falta la biblioteca para leer PDF. Instala las dependencias."
        ) from e

    # pypdf avisa por cada fuente recortada que no puede analizar del todo, y
    # en un cuadernillo son cientos de líneas que no le sirven a nadie. El
    # texto sale igual; lo comprobamos con el cuadernillo del ICFES.
    ruidoso = logging.getLogger("pypdf")
    nivel = ruidoso.level
    ruidoso.setLevel(logging.ERROR)
    try:
        lector = PdfReader(fichero)
        if getattr(lector, "is_encrypted", False):
            raise PdfIlegible(
                "El PDF está protegido con contraseña y no se puede leer."
            )
        paginas = [(p.extract_text() or "") for p in lector.pages]
    except PdfIlegible:
        raise
    except Exception as e:
        raise PdfIlegible(f"No se pudo leer el PDF ({type(e).__name__}).") from e
    finally:
        ruidoso.setLevel(nivel)

    # Las paginas van separadas por un salto de pagina, el caracter que existe
    # justo para esto. Hace falta despues: el mobiliario de la maqueta se
    # reconoce por estar al principio o al final de CADA pagina, y juntandolas
    # todas se pierde esa informacion.
    texto = "\f".join(paginas).strip()
    if not texto:
        raise PdfIlegible(
            "El PDF no tiene texto: probablemente es un escaneo, una imagen de "
            "las páginas. Habría que pasarle un reconocedor de texto antes."
        )
    return texto


def _aplanar(texto: str) -> str:
    """Quita saltos y ruido de maquetación, deja un párrafo continuo.

    Se aplana a propósito: en un PDF los saltos de línea son de la columna,
    no del contenido, y una pregunta parte en tres renglones no son tres
    cosas. Quien manda son los «1.» y los «a.».
    """
    paginas = [
        [l.strip() for l in p.splitlines() if l.strip()]
        for p in texto.split("\f")
    ]

    # El mobiliario de la maqueta —el encabezado con el nombre del módulo, el
    # pie, la entidad— se reconoce por DÓNDE está: arriba o abajo de cada
    # página, y repetido.
    #
    # El primer intento miraba solo si una línea se repetía, y se llevó por
    # delante «Excelente / Bueno / Regular / Malo»: en una encuesta esas
    # opciones salen en todas las preguntas, así que de 23 bloques quedaron 2.
    # Lo que distingue al mobiliario no es repetirse, es el sitio.
    bordes: dict[str, int] = {}
    for pagina in paginas:
        for linea in pagina[:2] + pagina[-2:]:
            if 3 <= len(linea) <= 90:
                bordes[linea] = bordes.get(linea, 0) + 1
    mobiliario = {l for l, n in bordes.items() if n >= 3}

    lineas = [l for pagina in paginas for l in pagina]
    utiles = [
        l for l in lineas
        if l and not RUIDO.match(l) and l not in mobiliario
    ]
    plano = re.sub(r"\s+", " ", " ".join(utiles))

    # Rachas de numeros sueltos —«4. 5. 6.»— que en un cuadernillo son los
    # numeros de pregunta, impresos en su propia columna.
    plano = re.sub(r"(?:(?<=\s)|^)(?:\d{1,3}\s*[.)]\s+){2,}", " ", plano)
    return re.sub(r"\s{2,}", " ", plano).strip()


def _trocear(plano: str) -> list[str]:
    """Los cuerpos de cada pregunta, cortando por las OPCIONES.

    El primer intento cortaba por los números —«1.», «2.»— y funcionaba con un
    documento escrito en Word, pero no con el cuadernillo del ICFES: allí los
    números de pregunta no están en el flujo del texto, van en otra capa de la
    maqueta. Sin ellos no había por dónde cortar y cada pregunta se tragaba la
    siguiente entera.

    Un documento de preguntas es, en realidad, una sucesión de
    `[enunciado][a][b][c][d][enunciado][a][b]…`. Así que se localizan todas
    las opciones y se agrupan: una nueva tanda empieza cuando la letra
    **retrocede** —de la d vuelve a la a—, que es la señal fiable de que
    empezó otra pregunta. Lo que queda entre una tanda y la siguiente es el
    enunciado de la segunda.
    """
    marcas = [(m.start(), m.group(1).lower(), m.end()) for m in OPCION.finditer(plano)]
    if not marcas:
        return []

    tandas: list[list[tuple[int, str, int]]] = [[marcas[0]]]
    for marca in marcas[1:]:
        anterior = tandas[-1][-1][1]
        if marca[1] <= anterior:
            tandas.append([marca])
        else:
            tandas[-1].append(marca)

    cuerpos = []
    arrastre = ""
    for posicion, tanda in enumerate(tandas):
        fin = tandas[posicion + 1][0][0] if posicion + 1 < len(tandas) else len(plano)
        inicio = tanda[0][0] if posicion else 0
        cuerpo = (arrastre + " " + plano[inicio:fin]).strip() if posicion else plano[:fin].strip()
        cuerpo, arrastre = _separar_enunciado_pegado(cuerpo)
        if cuerpo:
            cuerpos.append(cuerpo)
    return cuerpos


def _separar_enunciado_pegado(cuerpo: str) -> tuple[str, str]:
    """Despega del final el enunciado de la pregunta siguiente.

    Al aplanar, el enunciado de la pregunta N queda cosido al final de la
    ultima opcion de la N-1, porque entre ellos no hay mas separacion que un
    salto de linea que acabamos de quitar. Si no se separa, la opcion sale
    con un parrafo de mas y la pregunta siguiente sale «sin enunciado».

    La senial: un trozo final que **termina en «?» o en «:»** y que empieza
    despues de un punto. Es como acaba un enunciado y como no acaba una
    opcion. Si no se encuentra, no se parte nada: mejor una opcion larga que
    cortar una frase por la mitad.
    """
    # Si el documento numera sus preguntas, el numero ES la frontera y no hace
    # falta adivinar nada. Se busca de atras hacia delante y solo en lo que
    # viene despues de la primera opcion: un «1.» dentro del enunciado —«Paso
    # 1: abre el enlace»— no cuenta como principio de otra pregunta.
    desde = 0
    primera = OPCION.search(cuerpo)
    if primera:
        desde = primera.end()
    numeros = [m for m in PREGUNTA.finditer(cuerpo) if m.start() > desde]
    if numeros:
        ultimo = numeros[-1]
        cola = cuerpo[ultimo.start():].strip()
        if 10 <= len(cola) <= 700:
            return cuerpo[: ultimo.start()].strip(), cola

    if not (cuerpo.endswith("?") or cuerpo.endswith(":")):
        return cuerpo, ""
    for marca in reversed(list(re.finditer(r"(?<=[.!?])\s+(?=[¿A-ZÁÉÍÓÚÑ])", cuerpo))):
        cola = cuerpo[marca.end():].strip()
        if 25 <= len(cola) <= 700:
            return cuerpo[: marca.start()].strip(), cola
    return cuerpo, ""


def _convertir(cuerpo: str) -> str | None:
    """Un cuerpo de pregunta, en el formato del importador. None si no lo es."""
    cortes = [(m.start(), m.group(1).lower(), m.end()) for m in OPCION.finditer(cuerpo)]
    if len(cortes) < 2:
        # Sin al menos dos opciones no es una pregunta: será un encabezado o
        # un párrafo de instrucciones que empezaba por un número.
        return None

    # El numero con el que el documento ordena sus preguntas no es parte del
    # enunciado: si se deja, acaba guardado en la base y luego sale en la app
    # un «2.» que no significa nada, porque alli el orden es otro.
    #
    # Y lo que venga ANTES de ese numero tampoco es el enunciado. El numero es
    # la frontera que el propio documento pone: delante queda el pasaje de
    # lectura, o la portada entera —titulo, instrucciones, enlace de descarga,
    # los cinco pasos de instalacion— en el caso de la primera pregunta. Antes
    # todo eso se quedaba cosido al enunciado y habia que recortarlo a mano
    # desde la mitad de un parrafo. Va a «Contexto:», que es una linea que se
    # borra de un tiron si no servia.
    delante = cuerpo[: cortes[0][0]].strip()
    arranque = PREGUNTA.search(delante)
    anterior = ""
    if arranque and arranque.start() >= MINIMO_DE_CONTEXTO:
        anterior = delante[: arranque.start()].strip()
        delante = delante[arranque.start():]
    enunciado = PREGUNTA.sub("", delante, count=1).strip()
    opciones: list[list[str]] = []
    for i, (ini, letra, fin_marca) in enumerate(cortes):
        fin = cortes[i + 1][0] if i + 1 < len(cortes) else len(cuerpo)
        opciones.append([letra, cuerpo[fin_marca:fin].strip()])

    explicacion = ""
    correcta: str | None = None

    # La última opción suele arrastrar lo que venía después: la respuesta
    # suelta y la explicación, porque al aplanar se pegaron a ella.
    if opciones:
        cola = opciones[-1][1]
        m = EXPLICACION.search(cola)
        if m:
            explicacion = m.group(1).strip()
            cola = cola[: m.start()].strip()
        m = RESPUESTA_SUELTA.search(cola)
        if m:
            correcta = m.group(1).lower()
            cola = cola[: m.start()].strip()
        opciones[-1][1] = cola

    for letra, texto_opcion in opciones:
        if MARCA_EN_LA_OPCION.search(texto_opcion):
            correcta = letra

    contexto = anterior
    m = CONTEXTO.match(enunciado)
    if m:
        resto = m.group(1).strip()
        # El contexto va hasta donde empieza la pregunta de verdad, que suele
        # terminar en interrogación. Si no se distingue, se deja todo como
        # enunciado: mejor un enunciado largo que un contexto inventado.
        corte = resto.rfind("¿")
        if corte > 0:
            suyo, enunciado = resto[:corte].strip(), resto[corte:].strip()
        else:
            suyo, enunciado = "", resto
        contexto = " ".join(x for x in (contexto, suyo) if x)

    lineas = []
    if contexto:
        lineas.append("Contexto: " + contexto)
    lineas.append(enunciado or "(sin enunciado)")
    for letra, texto_opcion in opciones:
        limpio = MARCA_EN_LA_OPCION.sub("", texto_opcion).strip()
        lineas.append(("* " if letra == correcta else "- ") + limpio)
    if explicacion:
        lineas.append("> " + explicacion)
    return "\n".join(lineas)


def a_formato(texto: str) -> tuple[str, int]:
    """El texto de un PDF en el formato del importador, y cuántas salieron."""
    bloques = [b for b in (_convertir(c) for c in _trocear(_aplanar(texto))) if b]
    return "\n\n".join(bloques), len(bloques)


def leer(fichero) -> tuple[str, int]:
    """De un PDF al cuadro de texto de la pantalla de importar."""
    return a_formato(texto_de(fichero))
