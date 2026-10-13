# -*- coding: utf-8 -*-
"""Los primeros pasos de quien entra al panel por primera vez.

No es un tutorial decorativo. Las cuatro tareas son **lo que el panel necesita
que alguien haga**, así que la lista sigue sirviendo después del primer día:
mirar las cifras, cargar preguntas, cruzar datos y abrir la ficha de un
estudiante son el trabajo, no una demostración del trabajo.

POR QUÉ ASÍ Y NO CON GLOBOS SOBRE LA INTERFAZ
----------------------------------------------
La alternativa era una superposición que fuera señalando botones. Se descartó
por una razón concreta: para señalar «ese botón» hay que apuntar al HTML de
django-unfold, que es un paquete de terceros. En cuanto se actualice, la
visita apunta al vacío, y nadie se entera hasta que un superadministrador
nuevo ve globos flotando en mitad de la nada. Esta tarjeta no depende de una
sola clase ajena.

DÓNDE SE GUARDA
---------------
En la base y por usuario, no en el navegador. Con `localStorage` la visita se
repetiría al cambiar de equipo y desaparecería al limpiar el historial, que
son dos formas de mentir sobre si alguien ya la vio.
"""
from __future__ import annotations

from django.urls import reverse

#: Las claves son las que se guardan; cambiarlas equivale a reiniciar la
#: visita de todo el mundo, así que no se tocan a la ligera.
PASO_TABLERO = "tablero"
PASO_CARGA = "carga"
PASO_EXPLORADOR = "explorador"
PASO_ESTUDIANTE = "estudiante"

ORDEN = [PASO_TABLERO, PASO_CARGA, PASO_EXPLORADOR, PASO_ESTUDIANTE]

TEXTOS = {
    PASO_TABLERO: {
        "titulo": "Mira las cifras del programa",
        "texto": "Estudiantes, preguntas respondidas y racha media, al día con cada "
                 "sincronización de la app. Es esta misma pantalla.",
        "enlace": None,
        "boton": "",
    },
    PASO_CARGA: {
        "titulo": "Carga preguntas pegando texto",
        "texto": "Pegas las preguntas como las tengas escritas, el panel te enseña "
                 "qué entendió y solo guarda cuando lo confirmas.",
        "enlace": "admin:academics_question_importar",
        "boton": "Cargar preguntas",
    },
    PASO_EXPLORADOR: {
        "titulo": "Cruza los datos en el explorador",
        "texto": "Programa, competencia, nivel y fechas. Sirve para responder "
                 "«¿a quién le cuesta qué?» sin pedirle nada a nadie.",
        "enlace": "admin_explorador",
        "boton": "Abrir el explorador",
    },
    PASO_ESTUDIANTE: {
        "titulo": "Abre la ficha de un estudiante",
        "texto": "Su avance nivel a nivel y su historial de sincronizaciones, que "
                 "es lo que se mira cuando alguien deja de practicar.",
        "enlace": "admin_student_list",
        "boton": "Ver estudiantes",
    },
}


def _registro(usuario):
    """La fila del usuario, creándola si es su primera vez."""
    from .models import VisitaGuiada

    registro, _ = VisitaGuiada.objects.get_or_create(usuario=usuario)
    return registro


def marcar(usuario, paso: str) -> None:
    """Da un paso por hecho. Silencioso: nunca debe romper la vista que lo llama.

    Lo llaman las vistas de las que trata cada paso, así que se tacha porque
    la cosa se hizo de verdad y no porque alguien pulsara «entendido».
    """
    if not usuario or not usuario.is_authenticated or paso not in TEXTOS:
        return
    registro = _registro(usuario)
    if registro.hechos(paso):
        return
    registro.anotar(paso)


def estado(usuario) -> dict | None:
    """Qué enseñarle hoy, o None si no hay nada que enseñar.

    Devuelve None cuando la cerró a mano o cuando ya hizo las cuatro: una lista
    de tareas enteramente tachada deja de ser una ayuda y pasa a ser ruido.
    """
    if not usuario or not usuario.is_authenticated:
        return None

    registro = _registro(usuario)
    if registro.cerrada:
        return None

    pasos = []
    for clave in ORDEN:
        datos = TEXTOS[clave]
        pasos.append({
            "clave": clave,
            "titulo": datos["titulo"],
            "texto": datos["texto"],
            "boton": datos["boton"],
            "url": reverse(datos["enlace"]) if datos["enlace"] else "",
            "hecho": registro.hechos(clave),
        })

    hechos = sum(1 for p in pasos if p["hecho"])
    if hechos == len(ORDEN):
        return None

    return {"pasos": pasos, "hechos": hechos, "total": len(ORDEN)}


def se_puede_reabrir(usuario) -> bool:
    """Si tiene sentido ofrecer «volver a verlos».

    Solo cuando la escondio a mano y aun le quedan tareas. Ofrecer reabrir una
    lista enteramente tachada seria ofrecer nada.
    """
    if not usuario or not usuario.is_authenticated:
        return False
    registro = _registro(usuario)
    if not registro.cerrada:
        return False
    return any(not registro.hechos(c) for c in ORDEN)
