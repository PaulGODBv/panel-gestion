# -*- coding: utf-8 -*-
"""Lee preguntas escritas a mano y dice qué entendió de cada una.

El importador de CSV que había exigía conocer el **id numérico del nivel**, no
admitía explicación ni imagen —las tienen las 111 y 41 preguntas del banco,
respectivamente— y escribía sin enseñar antes lo que iba a escribir. Quien sube
las preguntas no es quien programó el panel, así que ese camino no lo usaba
nadie: las preguntas acababan entrando con guiones de Python.

Esto lee lo que de verdad tiene esa persona delante: el texto copiado de una
cartilla en PDF o de un Word. No hay columnas que cuadrar ni un formato que
aprenderse más allá de dos símbolos.

EL FORMATO
----------
Una línea en blanco separa una pregunta de la siguiente. Dentro de cada una:

    Contexto: el pasaje de lectura, si lo hay.
    El enunciado, que es todo lo que no lleva marca.
    * La opción correcta, con asterisco.
    - Las demás opciones, con guion.
    > La explicación, con mayor que.

El orden da igual y las marcas se pueden repetir en varias líneas: el contexto
y el enunciado largos se pueden partir en varios renglones y se vuelven a unir.

POR QUÉ CON MARCAS Y NO POR POSICIÓN
------------------------------------
La tentación era «la primera línea es el enunciado, las cuatro siguientes son
las opciones y la correcta va en tal sitio». Eso obliga a contar, y contar es
exactamente lo que fallaba en el CSV: `opcion_correcta (1-4)` era un número que
había que deducir mirando el orden en que se habían escrito las opciones. Con
el asterisco la respuesta correcta se marca **sobre la opción misma**, así que
no se puede descuadrar.

Este módulo no toca la base de datos ni importa Django a propósito: así se
puede ejecutar y probar solo, que es justo lo que no se podía hacer con el
importador anterior, metido dentro de una vista.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

#: Máximo de opciones por pregunta. Ocho no es un número redondo elegido al
#: azar: es lo que tienen las cinco preguntas de «Feelings», que comparten una
#: rejilla de parejas. Por debajo quedarían fuera del importador.
MAXIMO_OPCIONES = 8

MINIMO_OPCIONES = 2

ETIQUETA_CONTEXTO = re.compile(r"^contexto\s*:\s*", re.IGNORECASE)


@dataclass
class Opcion:
    texto: str
    correcta: bool = False


@dataclass
class Bloque:
    """Una pregunta leída del texto, con lo que se entendió y lo que no."""

    numero: int
    linea: int
    enunciado: str = ""
    contexto: str = ""
    explicacion: str = ""
    opciones: list[Opcion] = field(default_factory=list)

    #: Lo que impide crearla. Con un solo problema el bloque no se escribe.
    problemas: list[str] = field(default_factory=list)

    #: Lo que conviene saber pero no impide nada.
    avisos: list[str] = field(default_factory=list)

    #: Lo rellena quien consulta la base; aquí no se sabe.
    duplicada_de: int | None = None

    @property
    def valida(self) -> bool:
        return not self.problemas and self.duplicada_de is None

    @property
    def orden_de_la_correcta(self) -> int:
        """Posición 1..n de la correcta, que es como la guarda el modelo."""
        for i, opcion in enumerate(self.opciones, start=1):
            if opcion.correcta:
                return i
        return 0


def normalizar(texto: str) -> str:
    """Deja un texto comparable: sin tildes, sin mayúsculas y sin dobles espacios.

    Sirve para detectar que una pregunta ya está en el banco aunque se haya
    vuelto a teclear con otra puntuación. No se guarda: solo se compara.
    """
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", sin_tildes.lower())).strip()


def analizar(texto: str) -> list[Bloque]:
    """Convierte el texto pegado en bloques, cada uno con su diagnóstico."""
    bloques: list[Bloque] = []
    actual: Bloque | None = None
    enunciado: list[str] = []
    contexto: list[str] = []
    explicacion: list[str] = []

    def cerrar() -> None:
        nonlocal actual, enunciado, contexto, explicacion
        if actual is None:
            return
        actual.enunciado = " ".join(enunciado).strip()
        actual.contexto = " ".join(contexto).strip()
        actual.explicacion = " ".join(explicacion).strip()
        revisar(actual)
        bloques.append(actual)
        actual, enunciado, contexto, explicacion = None, [], [], []

    for numero_de_linea, cruda in enumerate(texto.splitlines(), start=1):
        linea = cruda.strip()

        if not linea:
            cerrar()
            continue

        if actual is None:
            actual = Bloque(numero=len(bloques) + 1, linea=numero_de_linea)

        if ETIQUETA_CONTEXTO.match(linea):
            contexto.append(ETIQUETA_CONTEXTO.sub("", linea).strip())
        elif linea.startswith(">"):
            explicacion.append(linea[1:].strip())
        elif linea.startswith("*"):
            actual.opciones.append(Opcion(linea[1:].strip(), correcta=True))
        elif linea.startswith("-"):
            actual.opciones.append(Opcion(linea[1:].strip()))
        else:
            enunciado.append(linea)

    cerrar()
    return bloques


def revisar(bloque: Bloque) -> None:
    """Anota en el bloque lo que lo impide y lo que solo conviene saber."""
    if not bloque.enunciado:
        bloque.problemas.append(
            "No hay enunciado: toda línea sin marca cuenta como enunciado, "
            "y aquí no quedó ninguna."
        )

    marcadas = [o for o in bloque.opciones if o.correcta]
    if not bloque.opciones:
        bloque.problemas.append(
            "No hay opciones. Van con «-» delante, y la correcta con «*»."
        )
    elif len(bloque.opciones) < MINIMO_OPCIONES:
        bloque.problemas.append(
            f"Solo hay una opción; hacen falta al menos {MINIMO_OPCIONES}."
        )
    elif len(bloque.opciones) > MAXIMO_OPCIONES:
        bloque.problemas.append(
            f"Hay {len(bloque.opciones)} opciones y el máximo es {MAXIMO_OPCIONES}. "
            "¿Se coló aquí la pregunta siguiente por faltar una línea en blanco?"
        )

    if bloque.opciones and not marcadas:
        bloque.problemas.append(
            "Ninguna opción lleva «*», así que no se sabe cuál es la correcta."
        )
    elif len(marcadas) > 1:
        bloque.problemas.append(
            f"Hay {len(marcadas)} opciones marcadas con «*» y solo puede haber una."
        )

    vacias = [o for o in bloque.opciones if not o.texto]
    if vacias:
        bloque.problemas.append(f"Hay {len(vacias)} opción(es) sin texto.")

    if not bloque.explicacion:
        bloque.avisos.append(
            "Sin explicación: en el modo de práctica no se verá el porqué de la "
            "respuesta. Las 111 preguntas del banco tienen una."
        )

    textos = [normalizar(o.texto) for o in bloque.opciones if o.texto]
    if len(textos) != len(set(textos)):
        bloque.avisos.append("Hay dos opciones que dicen lo mismo.")


def resumen(bloques: list[Bloque]) -> dict[str, int]:
    return {
        "total": len(bloques),
        "listas": sum(1 for b in bloques if b.valida),
        "con_problemas": sum(1 for b in bloques if b.problemas),
        "duplicadas": sum(1 for b in bloques if b.duplicada_de is not None),
        "con_avisos": sum(1 for b in bloques if b.avisos and b.valida),
    }
