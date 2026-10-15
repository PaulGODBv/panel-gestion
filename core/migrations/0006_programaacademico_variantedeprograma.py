"""El catálogo de programas y la tabla de variantes.

Esta migración solo crea estructura. La siembra de los 49 programas y el
reparto de los textos que ya están en la base van en la siguiente, separadas a
propósito: si algo sale mal al clasificar datos reales, se puede volver atrás
de los datos sin deshacer las tablas.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_visitaguiada"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProgramaAcademico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=140, unique=True, verbose_name="Nombre")),
                ("nivel", models.CharField(
                    choices=[("pregrado", "Pregrado"),
                             ("tecnologia", "Tecnología"),
                             ("tecnico", "Técnico laboral")],
                    max_length=20, verbose_name="Nivel")),
                ("activo", models.BooleanField(
                    default=True,
                    help_text="Desmárcalo si la Universidad retira el programa. Nunca lo "
                              "borres: hay reportes que apuntan a él.",
                    verbose_name="Activo")),
            ],
            options={
                "verbose_name": "Programa académico",
                "verbose_name_plural": "Programas académicos",
                "ordering": ["nivel", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="VarianteDePrograma",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("texto_normalizado", models.CharField(
                    max_length=160, unique=True, verbose_name="Texto normalizado")),
                ("texto_original", models.CharField(
                    max_length=160,
                    help_text="La primera grafía con la que llegó. Solo para reconocerla.",
                    verbose_name="Tal como se escribió")),
                ("programa", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="variantes",
                    to="core.programaacademico",
                    help_text="Vacío significa «sin asignar»: nadie ha dicho todavía a qué "
                              "programa corresponde, y los informes la muestran aparte.",
                    verbose_name="Programa")),
            ],
            options={
                "verbose_name": "Variante de programa",
                "verbose_name_plural": "Variantes de programa",
                "ordering": ["texto_normalizado"],
            },
        ),
        migrations.AddField(
            model_name="studentreport",
            name="variante_programa",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reportes",
                to="core.variantedeprograma",
                verbose_name="Programa (normalizado)"),
        ),
    ]
