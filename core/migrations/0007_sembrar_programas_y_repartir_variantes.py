"""Siembra los 49 programas y reparte lo que ya estaba escrito.

Lo que hace, en orden:

1. Crea los 49 programas del catálogo oficial.
2. Crea una variante por cada forma distinta en que algún reporte tenía escrito
   su programa, y engancha cada reporte a la suya.
3. Enlaza sola la variante cuyo nombre normalizado **coincide exactamente** con
   un programa. Ahí entran las mayúsculas y las tildes: «Ingeniería de
   software» queda enganchada a «Ingeniería de Software» sin que nadie decida
   nada, porque no hay nada que decidir.

Lo que NO hace es adivinar parecidos. «Admon Negocios Internacionales» se queda
sin asignar y sale marcada en el admin para que una persona la mapee. Fusionar
dos carreras porque se parecen mete un error en los resultados de la tesis sin
que nadie se entere, y un hueco visible siempre es mejor que un dato falso.

Al revés tampoco borra nada: `academic_program` se queda tal cual en cada
reporte, que es la evidencia de lo que el estudiante mandó.
"""

from django.db import migrations

from core.programas import CATALOGO, normalizar


def sembrar(apps, schema_editor):
    ProgramaAcademico = apps.get_model("core", "ProgramaAcademico")
    VarianteDePrograma = apps.get_model("core", "VarianteDePrograma")
    StudentReport = apps.get_model("core", "StudentReport")

    # 1. El catálogo.
    for nombre, nivel in CATALOGO:
        ProgramaAcademico.objects.get_or_create(
            nombre=nombre, defaults={"nivel": nivel, "activo": True}
        )

    # Un índice en memoria para no consultar 49 filas por cada variante.
    por_clave = {
        normalizar(p.nombre): p for p in ProgramaAcademico.objects.all()
    }

    # 2 y 3. Las variantes que ya existen en los datos.
    textos = (
        StudentReport.objects
        .exclude(academic_program__isnull=True)
        .exclude(academic_program="")
        .values_list("academic_program", flat=True)
        .distinct()
    )

    for texto in textos:
        clave = normalizar(texto)
        if not clave:
            continue
        variante, creada = VarianteDePrograma.objects.get_or_create(
            texto_normalizado=clave,
            defaults={"texto_original": texto.strip()[:160]},
        )
        programa = por_clave.get(clave)
        if creada and programa is not None:
            variante.programa = programa
            variante.save(update_fields=["programa"])

        StudentReport.objects.filter(academic_program=texto).update(
            variante_programa=variante
        )


def desandar(apps, schema_editor):
    """Suelta los reportes de sus variantes y vacía las dos tablas.

    Los reportes no pierden nada: su `academic_program` nunca se tocó.
    """
    StudentReport = apps.get_model("core", "StudentReport")
    VarianteDePrograma = apps.get_model("core", "VarianteDePrograma")
    ProgramaAcademico = apps.get_model("core", "ProgramaAcademico")

    StudentReport.objects.update(variante_programa=None)
    VarianteDePrograma.objects.all().delete()
    ProgramaAcademico.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_programaacademico_variantedeprograma"),
    ]

    operations = [
        migrations.RunPython(sembrar, desandar),
    ]
