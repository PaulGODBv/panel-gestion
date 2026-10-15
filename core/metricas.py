# -*- coding: utf-8 -*-
"""Las cuentas del panel, fuera de las vistas.

Viven aquí y no dentro de cada vista por una razón concreta: **la misma cifra
se enseñaba en dos sitios con dos valores distintos**. La lista de estudiantes
agregaba sobre el último reporte de cada uno y el tablero sobre todos, así que
el 12/10/2026 el tablero decía 2 015 preguntas cuando la cifra real eran 93.
Con una sola definición compartida, eso no puede volver a pasar.

LA REGLA DE ORO
---------------
**Un reporte es una foto, no un suceso.** Cada sincronización manda el estado
completo del estudiante —preguntas acumuladas, racha, progreso de cada nivel—,
así que la misma práctica reaparece en todas las fotos posteriores. Sumar
sobre todos los reportes cuenta la misma pregunta tantas veces como veces haya
sincronizado quien la respondió.

Por eso casi todo parte de [ultimos_reportes]. Las excepciones —cuántas
sincronizaciones hubo, el mapa de calor— son las que miden precisamente la
actividad de sincronización, y están señaladas allí donde se calculan.
"""
from __future__ import annotations

from django.db.models import Count, Max, Q, Sum

from .models import LevelProgressReport, StudentReport


#: Lo que se le pone detras a una variante que nadie ha mapeado todavia. Sale a
#: la vista a proposito: un hueco visible es mejor que un dato inventado, y es
#: lo que avisa de que hay algo que asignar en el admin.
SIN_ASIGNAR = " (sin asignar)"


def etiqueta_de_programa(nombre_canonico, texto_original):
    """Como se llama una fila de la tabla por programa.

    Tres casos, y los tres dicen una cosa distinta que no conviene mezclar:

    - Hay programa del catalogo: su nombre oficial.
    - Hay variante pero nadie la ha mapeado: lo que se escribio, marcado. Son
      los «Admon Negocios Internacionales» del mundo, que no se pueden asignar
      sin que una persona decida.
    - No hay ni variante: el estudiante no dijo su programa. Eso no es un
      programa desconocido, es la ausencia del dato, y merece su propia fila.
    """
    if nombre_canonico:
        return nombre_canonico
    if texto_original:
        return texto_original + SIN_ASIGNAR
    return "Sin programa"


def ultimos_reportes():
    """Un reporte por estudiante: el más reciente.

    Se desempata por `id` y no por `reported_at` porque dos sincronizaciones
    del mismo segundo —que las hay, la app reintenta— darían un empate que
    `Max` resolvería al azar.
    """
    ids = (
        StudentReport.objects
        .values("username")
        .annotate(ultimo=Max("id"))
        .values_list("ultimo", flat=True)
    )
    return StudentReport.objects.filter(id__in=list(ids))


def progreso_filtrado(programa="", competencia="", nivel="", desde=None, hasta=None):
    """Las filas de progreso que entran en un corte del explorador.

    Siempre sobre la última foto de cada estudiante. Los filtros vacíos no
    filtran, que es lo que permite que la pantalla abra enseñando el total.
    """
    reportes = ultimos_reportes()
    if programa:
        # Por el nombre del catalogo, no por el texto crudo: filtrar por
        # «Ingenieria de Software» tiene que traer tambien a quien lo escribio
        # en minusculas, que es el mismo estudiante de la misma carrera.
        reportes = reportes.filter(
            variante_programa__programa__nombre=programa
        )
    if desde:
        reportes = reportes.filter(reported_at__date__gte=desde)
    if hasta:
        reportes = reportes.filter(reported_at__date__lte=hasta)

    filas = LevelProgressReport.objects.filter(report__in=reportes)
    if competencia:
        filas = filas.filter(competence_id=competencia)
    if nivel:
        filas = filas.filter(level_id=nivel)
    return filas


def por_competencia(filas):
    """Acierto por competencia, ordenado de mejor a peor.

    El porcentaje se calcula **sobre los totales**, no promediando los
    porcentajes de cada nivel. No es lo mismo: un nivel de 2 preguntas pesaría
    igual que uno de 13, y el resultado diría más del reparto de niveles que
    de cómo le fue a nadie.
    """
    datos = (
        filas
        .values("competence_id", "competence_name")
        .annotate(
            aciertos=Sum("score"),
            preguntas=Sum("total_questions"),
            niveles=Count("id"),
            completados=Count("id", filter=Q(is_completed=True)),
            estudiantes=Count("report__username", distinct=True),
        )
        .order_by("competence_name")
    )

    salida = []
    for d in datos:
        preguntas = d["preguntas"] or 0
        aciertos = d["aciertos"] or 0
        salida.append({
            "id": d["competence_id"],
            "nombre": d["competence_name"],
            "aciertos": aciertos,
            "preguntas": preguntas,
            "porcentaje": round(aciertos * 100 / preguntas, 1) if preguntas else None,
            "niveles": d["niveles"],
            "completados": d["completados"],
            "estudiantes": d["estudiantes"],
        })

    # Las que no tienen ni una pregunta respondida van al final: no es que se
    # les de mal, es que nadie las ha tocado, y mezclarlas con un 0 % las
    # haria parecer lo primero.
    return sorted(
        salida,
        key=lambda c: (c["porcentaje"] is None, -(c["porcentaje"] or 0)),
    )


def mejor_y_peor(competencias):
    """La que mejor y la que peor se les da, de entre las que tienen datos.

    Es la «moda» que pedia TODO-6. Devuelve (None, None) cuando no hay con que
    compararlas: con una sola competencia respondida no hay mejor ni peor, hay
    una, y presentarla como ambas seria una conclusion inventada.
    """
    con_datos = [c for c in competencias if c["porcentaje"] is not None]
    if len(con_datos) < 2:
        return None, None
    return con_datos[0], con_datos[-1]


def por_programa(filas, columnas):
    """Media de acierto de cada programa, desglosada por competencia.

    Es la tabla cruzada que pedia TODO-6. `columnas` son los nombres de
    competencia en el orden en que los pinta la cabecera, y cada fila devuelve
    sus celdas **como lista en ese mismo orden**, no como diccionario: una
    plantilla de Django no sabe buscar en un diccionario por una clave
    variable, y forzarlo pedia inventar un filtro propio para algo que se
    arregla ordenando los datos aqui.

    Las celdas vacias van como None y no como cero: «nadie de este programa ha
    tocado esta competencia» y «la han tocado y han fallado todo» no son la
    misma noticia.
    """
    datos = (
        filas
        .values(
            # Se agrupa por el programa del catalogo, no por el texto que
            # escribio el estudiante. Antes, «Ingenieria de software» e
            # «Ingenieria de Software» salian como dos carreras distintas.
            "report__variante_programa__programa__nombre",
            "report__variante_programa__texto_original",
            "competence_name",
        )
        .annotate(aciertos=Sum("score"), preguntas=Sum("total_questions"))
    )

    crudo: dict[str, dict] = {}
    for d in datos:
        nombre = etiqueta_de_programa(
            d["report__variante_programa__programa__nombre"],
            d["report__variante_programa__texto_original"],
        )
        preguntas = d["preguntas"] or 0
        fila = crudo.setdefault(
            nombre, {"programa": nombre, "por_nombre": {}, "aciertos": 0, "preguntas": 0}
        )
        fila["por_nombre"][d["competence_name"]] = (
            round((d["aciertos"] or 0) * 100 / preguntas, 1) if preguntas else None
        )
        fila["aciertos"] += d["aciertos"] or 0
        fila["preguntas"] += preguntas

    salida = []
    for fila in crudo.values():
        salida.append({
            "programa": fila["programa"],
            "celdas": [fila["por_nombre"].get(c) for c in columnas],
            "media": (
                round(fila["aciertos"] * 100 / fila["preguntas"], 1)
                if fila["preguntas"] else None
            ),
        })
    return sorted(salida, key=lambda f: f["programa"])


def cobertura(filas):
    """Cuanta gente y cuantas preguntas hay detras del corte que se esta viendo.

    Va siempre junto al grafico. Un 80 % de acierto calculado sobre dos
    preguntas de un estudiante no significa nada, y sin este dato no hay forma
    de saberlo mirando las barras.
    """
    d = filas.aggregate(
        estudiantes=Count("report__username", distinct=True),
        preguntas=Sum("total_questions"),
        aciertos=Sum("score"),
    )
    preguntas = d["preguntas"] or 0
    return {
        "estudiantes": d["estudiantes"] or 0,
        "preguntas": preguntas,
        "aciertos": d["aciertos"] or 0,
        "porcentaje": round((d["aciertos"] or 0) * 100 / preguntas, 1) if preguntas else None,
    }
