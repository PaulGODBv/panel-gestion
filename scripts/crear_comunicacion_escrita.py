# -*- coding: utf-8 -*-
"""Da de alta Comunicacion Escrita como quinta competencia, con su primer nivel.

Viene de Desarrollo Estudiantil: «tambien incluyeme comunicacion escrita, ahi
tienes incluso ingles, asi que me falta esa». Las diez preguntas salen de
`Documents/Anteproyecto/Preguntas Comunicacion escrita.docx`.

**Discrepa del anteproyecto a proposito.** El documento comprometia «un nivel
especial integrado dentro de la competencia de Lectura Critica»; aqui va como
competencia aparte, que es como la trata el Icfes entre sus modulos genericos.
Es una de varias desviaciones aprobadas en la reunion —la otra es la
retroalimentacion— y toca reflejarlas en la memoria.

**Por que el modulo real no se puede reproducir.** La *Guia de orientacion,
modulos genericos, Saber Pro* dice que en Comunicacion Escrita «el tipo de
pregunta es abierta»: el evaluado redacta un texto argumentativo. Calificar
escritos uno a uno no es viable en la app y ademas rompe el ciclo de recompensa
inmediata que la sostiene. Se sustituye por items cerrados sobre los mismos
ejes: cohesion (conectores), precision lexica (adverbios) y correccion
gramatical (articulos).

De momento **un solo nivel**. Los grados de dificultad y los niveles de
evaluacion quedan pendientes de decidir, segun el usuario.

Uso:
    python scripts/crear_comunicacion_escrita.py            # ensayo
    python scripts/crear_comunicacion_escrita.py --aplicar  # escribe, con copia
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

from academics.models import Competence, Level, Question, QuestionOption  # noqa: E402

NOMBRE = "Comunicación Escrita"
DESCRIPCION = ("Cohesión, precisión léxica y corrección gramatical: los ejes con "
               "los que el Icfes califica el texto escrito.")
NIVEL = "Nivel 1 – Cohesión y corrección"
NIVEL_DESC = "Conectores, adverbios y artículos dentro de una frase con sentido."

# (enunciado, [opciones], posicion de la correcta 1-based, explicacion)
#
# Las explicaciones las redacte yo a partir de la categoria gramatical que trae
# cada pregunta en el .docx. Conviene que las revise quien escribio el banco.
PREGUNTAS = [
    ("Habíamos planeado pasar todo el fin de semana acampando en la montaña; _______, "
     "la fuerte tormenta del viernes nos obligó a cancelar el viaje y quedarnos en casa.",
     ["por consiguiente", "sin embargo", "además", "es decir"], 2,
     "Conector de contraste: la tormenta se opone al plan, no se deriva de él."),

    ("Para preparar una buena pasta, primero debes hervir el agua con un puñado de sal. "
     "_______, añade los espaguetis y revuelve suavemente para que no se peguen.",
     ["Anteriormente", "Quizás", "Luego", "Tampoco"], 3,
     "Adverbio de secuencia: marca el paso que viene después del primero."),

    ("Llegó casi cuarenta minutos tarde a su cita con el dentista _______ había un "
     "accidente terrible que bloqueó por completo la avenida principal.",
     ["aunque", "por lo tanto", "debido a que", "a pesar de que"], 3,
     "Conector de causa: el accidente es el motivo del retraso, no una concesión."),

    ("Estuve buscando por toda la casa durante un par de horas, hasta que por fin "
     "encontré _______ llaves del coche escondidas debajo de los cojines del sofá.",
     ["el", "las", "unas", "los"], 2,
     "Artículo definido en femenino plural: concuerda con «llaves» y son unas conocidas."),

    ("La película que vimos anoche en el cine de la esquina me pareció _______ aburrida; "
     "la trama era tan lenta que casi me quedo dormido a la mitad.",
     ["bastante", "nunca", "apenas", "felizmente"], 1,
     "Adverbio de cantidad: gradúa el adjetivo «aburrida»."),

    ("Estuvo ahorrando gran parte de su sueldo durante los últimos tres años; _______, "
     "pudo comprar el auto que tanto quería pagando todo al contado.",
     ["por lo tanto", "no obstante", "al contrario", "en cambio"], 1,
     "Conector de consecuencia: la compra es el resultado del ahorro."),

    ("Te prestaré mi chaqueta favorita para la fiesta de esta noche, _______ me prometas "
     "que la cuidarás mucho y no la mancharás con la comida.",
     ["siempre y cuando", "ya que", "por el contrario", "en resumen"], 1,
     "Conector de condición: el préstamo depende de que se cumpla la promesa."),

    ("Como estaba lloviendo a cántaros y la carretera de la autopista estaba muy "
     "resbaladiza, decidió conducir _______ para evitar cualquier tipo de accidente.",
     ["velozmente", "cautelosamente", "demasiado", "apenas"], 2,
     "Adverbio de modo: dice cómo se conduce, y el único coherente con evitar accidentes."),

    ("Fui al supermercado a comprar leche, pan y huevos para el desayuno de mañana. "
     "_______, pasé por la farmacia para comprar las vitaminas de la abuela.",
     ["En cambio", "Además", "Por el contrario", "Sin embargo"], 2,
     "Conector de adición: suma un recado más, no lo contrapone."),

    ("Todas las mañanas, antes de salir a pasear al perro por el parque del barrio, me "
     "gusta prepararme _______ buen café caliente para empezar el día con energía.",
     ["el", "la", "un", "una"], 3,
     "Artículo indefinido en masculino singular: concuerda con «café» y no es uno concreto."),
]


def main() -> int:
    aplicar = "--aplicar" in sys.argv

    ya = Competence.objects.filter(name=NOMBRE).first()
    if ya:
        print(f"«{NOMBRE}» ya existe (pk={ya.id}, order={ya.order}). Nada que hacer.")
        return 0

    orden = (Competence.objects.order_by("-order").first().order or 0) + 1
    print(f"Se creará «{NOMBRE}» con order={orden} -> id de app {orden}")
    print(f"  nivel: «{NIVEL}» con order=1 -> id de app {orden * 100 + 1}")
    print(f"  {len(PREGUNTAS)} preguntas, cada una con {len(PREGUNTAS[0][1])} opciones")
    for n, (texto, _, _, _) in enumerate(PREGUNTAS, 1):
        print(f"    {n:2}. {texto[:62]}...")

    if not aplicar:
        print("\nEnsayo. Nada escrito. Vuelve a lanzarlo con --aplicar.")
        return 0

    respaldo = BASE / f"db-antes-comunicacion-{datetime.now():%Y%m%d-%H%M}.sqlite3"
    shutil.copy2(BASE / "db.sqlite3", respaldo)
    print(f"\nCopia de seguridad: {respaldo.name}")

    competencia = Competence.objects.create(name=NOMBRE, description=DESCRIPCION, order=orden)
    nivel = Level.objects.create(
        competence=competencia,
        name=NIVEL,
        description=NIVEL_DESC,
        order=1,
        is_Locked_by_default=False,
        formato_practica=Level.FORMATO_OPCION,
    )

    for texto, opciones, correcta, explicacion in PREGUNTAS:
        pregunta = Question.objects.create(
            level=nivel,
            text=texto,
            explanation=explicacion,
            correct_option_order=correcta,
            is_active=True,
        )
        for i, opcion in enumerate(opciones, 1):
            QuestionOption.objects.create(question=pregunta, text=opcion, order=i)

    print(f"Competencia pk={competencia.id}, nivel pk={nivel.id}, "
          f"{nivel.questions.count()} preguntas.")
    print("\nFalta el lado Android: catálogo, migración de Room y NIVEL_DJANGO_A_APP.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
