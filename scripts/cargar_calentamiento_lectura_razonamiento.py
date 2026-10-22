# -*- coding: utf-8 -*-
"""Carga el calentamiento de Lectura Critica y Razonamiento Cuantitativo.

Los catorce items estan transcritos de `docs/preguntas-calentamiento-dos.md`,
que es donde se adaptaron y donde esta el criterio. Si hay que cambiar uno, se
cambia alli primero: ese documento es la fuente y esto es el transporte.

POR QUE EL CRITERIO NO ES EL DE CIUDADANAS. De las 55 preguntas de estas dos
competencias, 30 dependen de una imagen —26 de las 29 de Razonamiento—. Ahi el
contexto ya es corto y lo que pesa es la tabla, que no es prosa que se pueda
recortar: es el dato. Asi que en Razonamiento la tabla SE CONSERVA y se acorta
el enunciado; en Lectura se acorta el pasaje, y en varias ni hace falta porque
la pregunta ya cita dentro de si misma el fragmento que necesita.

LAS IMAGENES NO SE SUBEN: se reutiliza el `context_asset` de la pregunta
original, que ya esta en la base. Por eso cada item lleva de que pk la copia.

LO QUE NO HACE, Y ES DELIBERADO:

  * No toca ninguna pregunta de evaluacion. Las originales siguen enteras.
  * No resuelve los duplicados (pk26/pk83, pk23/pk78, pk13/pk72, pk18/pk77).
    Resolverlos es sacar preguntas de un nivel de evaluacion, y eso lo decide
    el autor del banco, no un guion.

Es idempotente: reconoce lo ya cargado por el texto del enunciado.

Uso:
    python scripts/cargar_calentamiento_lectura_razonamiento.py            # ensayo
    python scripts/cargar_calentamiento_lectura_razonamiento.py --aplicar  # escribe
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

from django.db import transaction  # noqa: E402

from academics.models import Competence, Level, Question, QuestionOption  # noqa: E402

# El pasaje de Hobbes recortado a las dos frases de las que cuelgan las cuatro
# ultimas preguntas de Lectura. El original son 574 caracteres con la cita
# bibliografica; esto son 248. Por debajo no se puede: sin estas dos frases no
# hay nada que leer criticamente.
#
# OJO: al reordenar la primera frase, el conector pasa de «sin embargo» a
# «pero». La pregunta 3 de Lectura pregunta por ese conector, asi que las dos
# cosas van juntas: si se restituye el pasaje largo, hay que restituir tambien
# el enunciado original.
HOBBES = (
    "«Las comodidades de la vida pueden aumentarse con la ayuda mutua; pero "
    "como eso se consigue mejor dominando a los demás que asociándose con "
    "ellos, nadie debe dudar de que los hombres, si no existiera el miedo, se "
    "inclinarían más al dominio que a la sociedad.\n\n"
    "El origen de las sociedades grandes y duraderas no está en la "
    "benevolencia mutua, sino en el miedo mutuo.»"
)

# Originales cuya imagen NO se hereda.
#
# `pk24` pregunta cuantas etiquetas salen de 2 presentaciones por 3 contenidos
# por 3 aromas. Los tres numeros estan en el enunciado, asi que su tabla —que
# ademas trae precios, que aqui no pintan nada— solo seria ruido. En un
# calentamiento, una tabla que no hace falta se lee igual: cuesta tiempo.
SIN_IMAGEN = {24}

# Cada entrada:
#   (pk del original, pasaje, enunciado, [cuatro opciones], correcta, porque)
#
# El pk del original NO es decorativo: de ahi se copia la imagen de contexto
# cuando la hay. `None` en el pasaje significa que la pregunta se sostiene sola.
#
# La posicion de la correcta es la MISMA que en el original, a proposito: asi
# la version corta y la larga se corresponden una a una.

RAZONAMIENTO = [
    (
        24, None,
        "Un jabón se hace en 2 presentaciones, con 3 contenidos cada una y en "
        "3 aromas. La etiqueta indica las tres cosas. ¿Cuántas etiquetas "
        "distintas hacen falta?",
        ["2", "6", "12", "18"],
        4,
        "Se multiplican las tres opciones, no se suman: 2 × 3 × 3 = 18. El 6 "
        "sale de multiplicar solo dos de ellas y el 12 de olvidar un aroma.",
    ),
    (
        20, None,
        "Reciclar una tonelada de papel ahorra 50.000 litros de agua. En una "
        "campaña de 20 días se recogen 2 toneladas diarias. ¿Cuánta agua se "
        "ahorra?",
        ["680 litros", "5.600 litros", "300.000 litros", "2.000.000 litros"],
        4,
        "2 × 20 = 40 toneladas, y 40 × 50.000 = 2.000.000. Las otras salen de "
        "usar el dato del petróleo, el de los árboles, o de multiplicar por "
        "los días pero no por las toneladas.",
    ),
    (
        21, None,
        "Se reciclan 150 toneladas de papel al día y cada tonelada ahorra 140 "
        "litros de petróleo. Alguien dice: «en un mes se ahorran 30 × 140 "
        "litros». Su afirmación es:",
        [
            "correcta, porque un mes tiene 30 días.",
            "incorrecta, porque olvida las 150 toneladas diarias.",
            "correcta, porque cada día se suman 140 litros más.",
            "incorrecta, porque olvida las 25 toneladas diarias.",
        ],
        2,
        "Los 140 litros son por tonelada, no por día. El error no está en el "
        "30 sino en haber perdido el otro factor. La cuarta ve el mismo fallo "
        "pero con el tonelaje mal: son 150 toneladas, el 25 % de 600, no 25.",
    ),
    (
        23, None,
        "¿En qué años se invirtió más?",
        [
            "1997, 1998, 1999 y 2000",
            "2000, 2001 y 2002",
            "1999, 2000 y 2001",
            "1996, 1997, 1998 y 1999",
        ],
        2,
        "Son las tres barras más altas, y están al final. Las otras opciones "
        "incluyen años del tramo bajo del principio.",
    ),
    (
        15, None,
        "¿Qué relación muestra la tabla entre magnitud y cantidad de sismos?",
        [
            "A mayor magnitud, mayor cantidad.",
            "A mayor magnitud, menor cantidad.",
            "A mayor cantidad, menor magnitud.",
            "A mayor cantidad, mayor magnitud.",
        ],
        2,
        "Se lee la tabla por columnas de magnitud y se ve que bajan. Las dos "
        "últimas invierten la pregunta: hablan de qué pasa con la magnitud "
        "según la cantidad, que no es lo que se mira.",
    ),
    (
        74, None,
        "El promedio anual fue 3.783 sismos. ¿Qué años quedan más cerca y más "
        "lejos del promedio?",
        ["2007 y 2010", "2006 y 2005", "2005 y 2002", "2002 y 2008"],
        2,
        "Hay que restar el promedio a cada año y comparar las diferencias, no "
        "buscar el mayor y el menor de la tabla — que es lo que llevan a hacer "
        "las otras opciones.",
    ),
    (
        22, None,
        "¿Cuánto más tarda el ave 5 alimentándose que desplazándose?",
        ["20 minutos", "25 minutos", "33 minutos", "45 minutos"],
        2,
        "Es una resta entre dos casillas de la misma fila. El 45 es el tiempo "
        "de alimentación sin restar, y el 20 el de desplazamiento.",
    ),
    (
        87, None,
        "Hay incentivo para quien venda más de $500.000 a la semana. ¿A quién "
        "le corresponde?",
        ["Solo I", "Solo III", "I y II", "I, II y III"],
        3,
        "Se compara cada fila con el umbral. La cuarta da por hecho que todos "
        "lo superan sin mirar, y la primera se queda en el primero que cumple.",
    ),
]

LECTURA = [
    (
        9, None,
        "«La búsqueda de la Justicia es la eterna búsqueda de la felicidad "
        "humana». De esa frase se concluye que:",
        [
            "quien busca la justicia no encuentra la felicidad.",
            "quien busca la justicia también busca la felicidad.",
            "quien busca la justicia nunca encuentra la felicidad.",
            "quien busca la justicia siempre encuentra la felicidad.",
        ],
        2,
        "La frase habla de buscar, no de encontrar. Las otras tres cambian la "
        "búsqueda por un resultado —que se encuentre, que no, que siempre— y "
        "eso la frase no lo dice.",
    ),
    (
        14, None,
        "Luisa dice: «Si estoy con un man que me gusta porque sí, ¿por qué no "
        "voy a estar con otro por plata?». Eso implica que ella:",
        [
            "decide dentro de las normas de su comunidad.",
            "no pone los sentimientos por encima del dinero.",
            "prefiere a los hombres con dinero.",
            "le da importancia a la opinión de los demás.",
        ],
        2,
        "Equipara las dos razones, no dice que prefiera una. La tercera es la "
        "lectura apresurada: que las iguale no significa que escoja el dinero.",
    ),
    (
        10, HOBBES,
        "¿Qué función cumple el «pero» de la primera frase?",
        [
            "Aclara que dominar aumenta las comodidades.",
            "Desmiente que la ayuda mutua las aumente.",
            "Contrasta la ayuda mutua con el dominio, más eficaz.",
            "Cuestiona que la ayuda mutua las aumente.",
        ],
        3,
        "El texto no niega que la ayuda mutua sirva —dice que la otra vía "
        "sirve más—, así que ni desmiente ni cuestiona: contrapone.",
    ),
    (
        11, HOBBES,
        "El autor dice (i) que el miedo origina las sociedades, y (ii) que sin "
        "miedo el hombre buscaría dominar. ¿Qué relación hay entre las dos?",
        [
            "(i) es premisa y (ii) conclusión.",
            "(ii) es premisa y (i) conclusión.",
            "Las dos son premisas del mismo argumento.",
            "Las dos dicen la misma conclusión.",
        ],
        3,
        "Ninguna se deduce de la otra; las dos sostienen la misma tesis. Que "
        "vayan seguidas no las convierte en premisa y conclusión.",
    ),
    (
        68, HOBBES,
        "¿Cuál es la antítesis de la tesis del texto?",
        [
            "Las sociedades nacen de la desconfianza entre los hombres.",
            "Las sociedades nacen de la indiferencia entre los hombres.",
            "Las sociedades nacen de la obediencia recíproca.",
            "Las sociedades nacen de la colaboración desinteresada.",
        ],
        4,
        "La tesis es que nacen del miedo. Lo contrario del miedo aquí no es la "
        "calma sino la confianza: colaborar sin esperar nada. La desconfianza "
        "es casi lo mismo que el miedo, no su contrario.",
    ),
    (
        72, HOBBES,
        "Si los hombres se inclinan más al dominio que a la sociedad, ¿por qué "
        "viven en comunidad?",
        [
            "Para dominar de forma colectiva y más segura.",
            "Para ampliar su capacidad de dominio.",
            "Para evitar el dominio mediante relaciones confiables.",
            "Porque buscan seguridad frente al dominio de otros.",
        ],
        4,
        "No entran en sociedad para dominar mejor sino para no ser dominados. "
        "Las dos primeras convierten el miedo en estrategia.",
    ),
]

LOTES = [
    ("Razonamiento Cuantitativo", RAZONAMIENTO),
    ("Lectura Crítica", LECTURA),
]


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    plan = []

    for nombre_competencia, items in LOTES:
        competencia = Competence.objects.filter(name=nombre_competencia).first()
        if competencia is None:
            print(f"No existe la competencia «{nombre_competencia}». Se aborta.")
            return 1

        nivel = Level.objects.filter(competence=competencia, order=0).first()
        if nivel is None:
            print(f"«{nombre_competencia}» no tiene nivel de calentamiento.")
            print("Crealo antes con scripts/crear_niveles_de_practica.py")
            return 1

        print(f"\n{competencia.name}")
        print(f"  nivel {nivel.name} (pk={nivel.id}), ahora con "
              f"{nivel.questions.count()} preguntas")

        existentes = set(
            Question.objects.filter(level=nivel).values_list("text", flat=True)
        )

        for pk_origen, pasaje, texto, opciones, correcta, porque in items:
            if texto in existentes:
                print(f"    = ya estaba: {texto[:56]}…")
                continue

            origen = Question.objects.filter(pk=pk_origen).first()
            if origen is None:
                print(f"    ! no existe la original pk{pk_origen}, se omite")
                continue

            imagen = None if pk_origen in SIN_IMAGEN else origen.context_asset
            plan.append((nivel, pasaje, texto, opciones, correcta, porque, imagen))
            print(f"    + {texto[:56]}…")
            print(f"        correcta: {correcta}. {opciones[correcta - 1][:44]}")
            if imagen:
                print(f"        conserva la imagen de pk{pk_origen}")

    if not plan:
        print("\nNada que hacer.")
        return 0

    print(f"\nSe aniadirian {len(plan)} preguntas.")

    if not aplicar:
        print("Ensayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    base_sqlite = BASE / "db.sqlite3"
    if base_sqlite.is_file():
        respaldo = BASE / f"db-antes-calentamiento2-{datetime.now():%Y%m%d-%H%M}.sqlite3"
        shutil.copy2(base_sqlite, respaldo)
        print(f"\nCopia de seguridad: {respaldo.name}")
    else:
        print("\nAVISO: no hay db.sqlite3, asi que NO se ha hecho copia.")
        print("Si esto corre contra PostgreSQL, respalda antes por tu cuenta.")

    # Todo o nada: media carga deja dos niveles a medias y sin forma de saber
    # cuales faltan sin compararlas a mano.
    with transaction.atomic():
        for nivel, pasaje, texto, opciones, correcta, porque, imagen in plan:
            pregunta = Question.objects.create(
                level=nivel,
                text=texto,
                reading_text=pasaje or "",
                explanation=porque,
                correct_option_order=correcta,
                context_asset=imagen,
                is_active=True,
            )
            for posicion, opcion in enumerate(opciones, start=1):
                QuestionOption.objects.create(
                    question=pregunta, text=opcion, order=posicion
                )

    print(f"\nCargadas {len(plan)}.")
    for nombre_competencia, _ in LOTES:
        nivel = Level.objects.get(competence__name=nombre_competencia, order=0)
        print(f"  {nombre_competencia}: {nivel.questions.count()} preguntas")

    print("\nQueda pendiente, y no lo hace este guion:")
    print("  * Los duplicados: pk26/pk83 —identicas—, pk23/pk78, pk13/pk72,")
    print("    pk18/pk77. Siguen vivos en los niveles de evaluacion.")
    print("  * El calentamiento de Ingles, aun vacio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
