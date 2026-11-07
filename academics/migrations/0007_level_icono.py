# -*- coding: utf-8 -*-
"""El icono del nivel, guardado en la base.

Escrita a mano, como todas las de este proyecto, y sin borrar nada: los dos
campos son nuevos y aceptan nulo, así que los 18 niveles que ya existen
quedan exactamente como estaban y siguen pintando el icono compilado en el
APK. Un nivel sin icono propio no es un nivel roto: es uno que todavía no lo
tiene.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0006_alter_competence_description_alter_competence_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="level",
            name="icono",
            field=models.BinaryField(
                blank=True,
                editable=False,
                help_text="PNG cuadrado de 256 px, normalizado al subirlo.",
                null=True,
                verbose_name="Icono",
            ),
        ),
        migrations.AddField(
            model_name="level",
            name="icono_version",
            field=models.PositiveIntegerField(
                default=0,
                editable=False,
                verbose_name="Version del icono",
            ),
        ),
    ]
