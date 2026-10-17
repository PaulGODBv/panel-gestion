# -*- coding: utf-8 -*-
"""Carga las preguntas de calentamiento de Competencias Ciudadanas.

Las dieciseis estan transcritas de `docs/preguntas-calentamiento.md`, que es
donde se adaptaron y donde esta el criterio con el que se acortaron. Si hay que
cambiar una, se cambia alli primero: ese documento es la fuente y esto es el
transporte.

POR QUE EXISTE ESTE GUION. Los cuatro niveles «Calentamiento» se crearon
publicados y VACIOS. En la app, la tarjeta de calentamiento sale siempre que el
nivel exista, asi que un estudiante la toca y se encuentra un nivel sin
preguntas. Esto llena el de Ciudadanas; los otros tres siguen vacios.

LO QUE NO HACE, Y ES DELIBERADO:

  * No toca ni una pregunta de los niveles de evaluacion. Las originales siguen
    enteras donde estan: estas son versiones cortas que se **aniaden**.
  * No resuelve los duplicados del banco (`q95`/`q50`, `q57`/`q58`,
    `q51`/`q96`). Resolverlos es sacar preguntas de un nivel de evaluacion, y
    eso lo decide el autor del banco, no un guion.
  * No mueve las dos cortas que ya existen (`q58`, `q96`). Mismo motivo.

Es idempotente: reconoce lo ya cargado por el texto del enunciado y lo omite,
asi que lanzarlo dos veces no duplica nada.

Uso:
    python scripts/cargar_calentamiento_ciudadanas.py            # ensayo
    python scripts/cargar_calentamiento_ciudadanas.py --aplicar  # escribe
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

COMPETENCIA = "Competencias Ciudadanas"

# Cada entrada: (enunciado, [cuatro opciones], posicion de la correcta, porque).
#
# La posicion es 1..4 y es la MISMA que tenia el original, a proposito: asi la
# version corta y la larga se corresponden una a una y `correct_option_order`
# no hay que recalcularlo a mano.
PREGUNTAS = [
    (
        "En época de lluvias se inundan las escuelas rurales. ¿Cuál de estas "
        "soluciones vulnera el derecho a la educación?",
        [
            "Llevar a los niños en transporte a escuelas no afectadas.",
            "Dar clases los sábados y parar en temporada de lluvias.",
            "Enviar tutores a domicilio algunos días.",
            "Asistir dos veces por semana y reducir el total de clases.",
        ],
        4,
        "Las tres primeras mantienen las horas de clase y solo cambian cómo se "
        "llega a ellas. La cuarta recorta el total, y ahí está la vulneración.",
    ),
    (
        "Se propone una ley que condena el satanismo por ir contra las "
        "creencias de la mayoría. ¿Por qué no podría aprobarse?",
        [
            "Porque la Constitución protege todas las creencias, no solo las de la mayoría.",
            "Porque obligaría a renunciar a los congresistas de religiones minoritarias.",
            "Porque la religión es asunto de las iglesias y no de los Estados.",
            "Porque las leyes actuales hacen de la religión un asunto privado.",
        ],
        1,
        "La libertad de cultos no se decide por mayorías; la Constitución iguala "
        "todas las confesiones. El punto es ese, no quién legisla ni dónde se practica.",
    ),
    (
        "Se discute reformar la Constitución para permitir la pena de muerte. "
        "¿Pueden los ciudadanos pronunciarse directamente?",
        [
            "No, los asuntos penales son solo de la Rama Judicial.",
            "No, lo decide el presidente por decreto.",
            "Sí, mediante un referendo constitucional.",
            "No, solo el Congreso puede reformarla.",
        ],
        3,
        "El referendo constitucional existe justamente para que la ciudadanía "
        "decida una reforma. El Congreso también puede, pero no en exclusiva.",
    ),
    (
        "La Corte Constitucional extendió a las parejas del mismo sexo la salud "
        "y la pensión de sobrevivientes. ¿Qué argumento respalda esa decisión?",
        [
            "Garantizar la igualdad de derechos entre todos los ciudadanos.",
            "Proteger los derechos de los pensionados.",
            "Proteger los derechos del matrimonio entre hombre y mujer.",
            "La Constitución no reconoce esos derechos patrimoniales.",
        ],
        1,
        "La Corte se apoyó en el principio de igualdad. La cuarta opción, además, "
        "contradice la decisión que se está explicando.",
    ),
    (
        "Se culpa a los policías de tránsito de las congestiones porque siempre "
        "hay uno donde hay trancón. ¿Qué argumento contradice esa postura?",
        [
            "No se les debe cuestionar porque representan a una institución.",
            "Que estén donde hay congestión no significa que la causen.",
            "Hacen su labor, pero no alcanzan para evitarlas.",
            "Que haya congestión no significa que no estén capacitados.",
        ],
        2,
        "Confundir coincidencia con causa es una falacia. La segunda opción la "
        "nombra; las demás aceptan el vínculo y solo lo matizan.",
    ),
    (
        "El Gobierno pide aportes a la ciudadanía tras una inundación y casi "
        "nadie responde. Según la Constitución, eso refleja:",
        [
            "Incapacidad del Gobierno para atender la emergencia.",
            "Fallas en la infraestructura de prevención.",
            "Falta de solidaridad de los ciudadanos.",
            "Desconfianza en las instituciones.",
        ],
        3,
        "Las otras tres culpan al Estado o a las instituciones. La pregunta es "
        "por la conducta de los ciudadanos, y la Constitución la nombra: solidaridad.",
    ),
    (
        "Un periódico danés publicó caricaturas de Mahoma y muchos musulmanes "
        "protestaron. ¿Qué aspectos entran en conflicto?",
        [
            "Las democracias europeas y las teocracias orientales.",
            "Las religiones occidentales y las orientales.",
            "La libertad de expresión y las creencias religiosas.",
            "Los valores de Europa y las tradiciones de África y Asia.",
        ],
        3,
        "El choque es entre dos derechos, no entre dos bloques de países ni dos "
        "religiones. Las otras opciones cambian el conflicto de escala.",
    ),
    (
        "Algunos proponen legalizar las drogas para defender el bien común. "
        "¿Cuál argumento está a favor de esa propuesta?",
        [
            "La violencia se asocia al tráfico, así que hay que controlar su comercio.",
            "La responsabilidad es de los países consumidores, no de los productores.",
            "Quien consume está enfermo y el Estado debe darle un ambiente sano.",
            "La prohibición causó problemas sociales peores que los que evitaba.",
        ],
        4,
        "Solo la cuarta defiende legalizar. La primera pide control, que es lo "
        "contrario; las otras dos hablan de culpa y de tratamiento, que es otro debate.",
    ),
    (
        "El alcalde evalúa cerrar barrios enteros con seguridad privada, con "
        "entrada solo para residentes. ¿Qué intereses chocan?",
        [
            "Las empresas de seguridad y los residentes que soportarían controles.",
            "La seguridad de los residentes y el acceso de todos al espacio público.",
            "El beneficio de los residentes y el deber del gobierno local.",
            "Las empresas de seguridad que serían contratadas.",
        ],
        2,
        "Cerrar un barrio privatiza calles que son de todos. Las demás opciones "
        "describen a los actores, pero no el bien que se pierde.",
    ),
    (
        "Activistas piden parar los experimentos con cerdos; los científicos "
        "responden que así evitan arriesgar vidas humanas. ¿En qué difieren?",
        [
            "Los activistas se oponen al desarrollo; los científicos quieren mejorar la vida.",
            "Los activistas dudan de la ciencia; los científicos evaden el control.",
            "Los científicos usan animales como instrumentos; los activistas quieren que se les tenga apego.",
            "Los científicos priorizan la vida humana; los activistas, el derecho del animal a la suya.",
        ],
        4,
        "La diferencia es sobre qué vida se pone primero. Las otras tres atribuyen "
        "intenciones que ninguna de las dos partes expresó.",
    ),
    (
        "Una paciente firmó el consentimiento para transfusiones, pero tras la "
        "cirugía las rechaza por su religión. ¿Qué dimensión está privilegiando?",
        [
            "Sus creencias religiosas y el modo de vida que exigen.",
            "Las consecuencias futuras en su salud.",
            "Las recomendaciones médicas y la evidencia científica.",
            "La decisión de su familia.",
        ],
        1,
        "Rechaza lo que ella misma había firmado y lo que le recomiendan. Lo único "
        "que queda por encima de ambas cosas es su creencia.",
    ),
    (
        "El FMI dice que a América Latina le falta innovación tecnológica. Una "
        "analista responde que el problema real es que la mitad de las mujeres "
        "trabaja en el hogar sin salario. Ese argumento:",
        [
            "respalda al FMI: hay potencial femenino sin aprovechar para tecnificar la región.",
            "refuta al FMI: el obstáculo principal es la desigualdad, no la tecnología.",
            "rechaza al FMI: la innovación no influye en el desarrollo.",
            "apoya al FMI: ambos muestran más participación femenina.",
        ],
        2,
        "La analista no niega que la tecnología sirva, señala otra causa como "
        "principal. Por eso refuta y no rechaza; esa es toda la pregunta.",
    ),
    (
        "La capital construirá su relleno sanitario en un municipio vecino, con "
        "todas las licencias y pagando compensación. En consulta popular, los "
        "habitantes votan en contra. ¿Qué entra en conflicto?",
        [
            "El medio ambiente de la capital y la voluntad del gobierno departamental.",
            "La economía del municipio y las políticas ambientales de la capital.",
            "La salubridad de la capital y la voluntad de los habitantes del municipio.",
            "El interés comercial del gobierno y el bienestar del municipio.",
        ],
        3,
        "Todo es legal y aun así hay conflicto. Lo que choca con la necesidad de "
        "la capital es una decisión democrática, no un trámite pendiente.",
    ),
    (
        "Un juez alemán prohíbe la circuncisión en menores de 14 años. Las "
        "comunidades judía y musulmana lo ven como un ataque a sus creencias. "
        "El texto pone el énfasis en:",
        [
            "Las consecuencias económicas de discriminar a un pueblo.",
            "El efecto en las relaciones internacionales de Alemania.",
            "Las creencias y tradiciones que respaldan la práctica.",
            "Las medidas judiciales contra las religiones minoritarias.",
        ],
        3,
        "Se pregunta por el énfasis del texto, no por quién tiene razón. El texto "
        "habla de siglos de tradición, no de economía ni de diplomacia.",
    ),
    (
        "Un gerente ofrece 100 empleos, pero solo para nacidos en tierra fría, "
        "«porque los de tierra caliente no trabajan igual». ¿Qué consecuencia tendría?",
        [
            "La junta directiva lo respaldaría por seleccionar a los mejores.",
            "Los empresarios lo respaldarían por el empleo que se crea.",
            "El Gobierno se opondría por el uso del beneficio tributario.",
            "Los trabajadores se opondrían porque parte de un prejuicio.",
        ],
        4,
        "El criterio no es lo que cada persona sabe hacer, sino dónde nació. Eso "
        "es un prejuicio, y es a lo que se opondrían los trabajadores.",
    ),
    (
        # El 15/10 esta llevaba un contexto RECONSTRUIDO, deducido de las
        # opciones porque el original no aparecia por ninguna parte. Medía la
        # idea correcta —desplazar la culpa— pero NO era la escena: hablaba de
        # una mujer que «se expuso» al salir sola de noche, y en la pregunta de
        # verdad el funcionario no habla de ninguna victima concreta, sino que
        # desacredita un estudio.
        #
        # El 16/10 se recupero el pasaje del cuadernillo oficial del ICFES
        # —«Modulo de Competencias ciudadanas, Saber Pro 2018»— y esta version
        # sale de ahi. Un contexto deducido se parece lo justo para colar y lo
        # bastante para estar mal.
        "Un estudio dice que el 30 % de las mujeres en Colombia sufre violencia "
        "física. Un funcionario responde que no es confiable y que hay que ver "
        "la justificación de los hechos. Eso puede llevar a que:",
        [
            "se cuestione a los investigadores del estudio.",
            "se entiendan mejor las estrategias de prevención.",
            "se reconozca la gravedad de la violencia.",
            "se minimice la responsabilidad del agresor.",
        ],
        4,
        "Buscar qué hizo la víctima desplaza la culpa. Esa es la consecuencia, "
        "aunque quien habla no la pretenda.",
    ),
]


def main() -> int:
    aplicar = "--aplicar" in sys.argv

    competencia = Competence.objects.filter(name=COMPETENCIA).first()
    if competencia is None:
        print(f"No existe la competencia «{COMPETENCIA}». Se aborta.")
        return 1

    nivel = Level.objects.filter(competence=competencia, order=0).first()
    if nivel is None:
        print("Esa competencia no tiene nivel de calentamiento (order=0).")
        print("Crealo antes con scripts/crear_niveles_de_practica.py")
        return 1

    print(f"Competencia: {competencia.name} (pk={competencia.id})")
    print(f"Nivel:       {nivel.name} (pk={nivel.id}, order={nivel.order})")
    print(f"Tiene ahora: {nivel.questions.count()} preguntas\n")

    # Se reconoce lo ya cargado por el enunciado: es lo unico estable entre una
    # ejecucion y otra, porque los ids los pone la base.
    existentes = set(
        Question.objects.filter(level=nivel).values_list("text", flat=True)
    )

    nuevas = [p for p in PREGUNTAS if p[0] not in existentes]
    repetidas = len(PREGUNTAS) - len(nuevas)

    for texto, opciones, correcta, _ in nuevas:
        print(f"  + {texto[:66]}…")
        print(f"      correcta: {correcta}. {opciones[correcta - 1][:52]}")

    if repetidas:
        print(f"\n  {repetidas} ya estaban cargadas; se omiten.")

    if not nuevas:
        print("\nNada que hacer.")
        return 0

    print(f"\nSe aniadirian {len(nuevas)} preguntas.")

    if not aplicar:
        print("Ensayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    base_sqlite = BASE / "db.sqlite3"
    if base_sqlite.is_file():
        respaldo = BASE / f"db-antes-calentamiento-{datetime.now():%Y%m%d-%H%M}.sqlite3"
        shutil.copy2(base_sqlite, respaldo)
        print(f"\nCopia de seguridad: {respaldo.name}")
    else:
        # En produccion la base es PostgreSQL y la copia no es cosa de un
        # `cp`. Se avisa en vez de seguir como si se hubiera hecho.
        print("\nAVISO: no hay db.sqlite3, asi que NO se ha hecho copia.")
        print("Si esto corre contra PostgreSQL, respalda antes por tu cuenta.")

    # Todo o nada: media carga deja el nivel con preguntas sueltas y sin forma
    # de saber cuales faltan sin compararlas a mano.
    with transaction.atomic():
        for texto, opciones, correcta, explicacion in nuevas:
            pregunta = Question.objects.create(
                level=nivel,
                text=texto,
                reading_text="",
                explanation=explicacion,
                correct_option_order=correcta,
                is_active=True,
            )
            for posicion, opcion in enumerate(opciones, start=1):
                QuestionOption.objects.create(
                    question=pregunta, text=opcion, order=posicion
                )

    print(f"\nCargadas {len(nuevas)}. El nivel queda con {nivel.questions.count()}.")
    print("\nQueda pendiente, y no lo hace este guion:")
    print("  * Los duplicados del banco: q95/q50, q57/q58, q51/q96.")
    print("  * El pasaje real de q100, que hay que sacar de la cartilla.")
    print("  * El calentamiento de las otras tres competencias, aun vacio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
