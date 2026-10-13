# -*- coding: utf-8 -*-
"""Pruebas de las cifras del panel y de lo que se enseña cuando no hay ninguna.

Las dos cosas van juntas porque las dos se descubrieron el mismo día: el
tablero sumaba sobre todos los reportes —decía 2 015 preguntas donde había 93—
y nadie se había parado a mirar cómo queda el panel después de la purga que
precede al piloto.

La de la suma es una prueba de regresión en el sentido estricto: reproduce el
fallo tal como era, con un estudiante que sincroniza varias veces, y falla si
alguien vuelve a agregar sobre todos los reportes.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import LevelProgressReport, StudentReport


class CifrasDelTableroTest(TestCase):
    """Un reporte es una foto, no un suceso."""

    def setUp(self):
        # Un estudiante que sincroniza tres veces. En cada foto va su
        # acumulado, no lo hecho desde la anterior: 10, luego 25, luego 40.
        for total, racha in ((10, 1), (25, 2), (40, 3)):
            reporte = StudentReport.objects.create(
                username="ana",
                email="ana@mail.udes.edu.co",
                total_questions_answered=total,
                current_streak_days=racha,
                academic_program="Enfermería",
            )
            LevelProgressReport.objects.create(
                report=reporte,
                competence_name="Lectura Crítica",
                level_name="Nivel 1",
                competence_id=1,
                level_id=101,
                score=total // 2,
                total_questions=total,
                is_completed=False,
            )

    def test_las_preguntas_no_se_suman_una_vez_por_sincronizacion(self):
        from .views import DashboardDataAPIView
        from django.test import RequestFactory

        datos = DashboardDataAPIView().get(RequestFactory().get("/")).data

        # 40, su último acumulado. Sumando las tres fotos darían 75.
        self.assertEqual(datos["total_questions"], 40)
        self.assertEqual(datos["total_students"], 1)
        # Las sincronizaciones sí se cuentan todas: es lo que mide esa tarjeta.
        self.assertEqual(datos["total_reports"], 3)
        # La racha es la de la última foto, no el promedio de las tres (que
        # daría 2).
        self.assertEqual(datos["avg_streak"], 3.0)

    def test_el_progreso_por_competencia_no_cuenta_el_mismo_nivel_tres_veces(self):
        from .views import DashboardDataAPIView
        from django.test import RequestFactory

        datos = DashboardDataAPIView().get(RequestFactory().get("/")).data
        competencias = datos["competence_progress"]

        self.assertEqual(len(competencias), 1)
        self.assertEqual(competencias[0]["total"], 1)

    def test_el_explorador_usa_la_misma_definicion(self):
        from .metricas import cobertura, por_competencia, progreso_filtrado

        filas = progreso_filtrado()
        self.assertEqual(cobertura(filas)["preguntas"], 40)
        self.assertEqual(por_competencia(filas)[0]["porcentaje"], 50.0)


class PanelVacioTest(TestCase):
    """Cómo se ve el panel tras la purga que precede al piloto."""

    def setUp(self):
        self.client.force_login(
            get_user_model().objects.create_superuser(
                "staff", "staff@mail.udes.edu.co", "irrelevante-para-la-prueba"
            )
        )

    def test_la_api_avisa_de_que_no_hay_nada(self):
        from .views import DashboardDataAPIView
        from django.test import RequestFactory

        datos = DashboardDataAPIView().get(RequestFactory().get("/")).data
        self.assertTrue(datos["panel_vacio"])
        self.assertEqual(datos["total_questions"], 0)

    def test_el_explorador_explica_que_falta(self):
        respuesta = self.client.get(reverse("admin_explorador"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Todavía no hay nada que cruzar")
        self.assertContains(respuesta, "practique y la app sincronice")

    def test_la_lista_de_estudiantes_explica_que_falta(self):
        respuesta = self.client.get(reverse("admin_student_list"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Aún no hay estudiantes")

    def test_el_explorador_distingue_vacio_de_filtrado_a_cero(self):
        """Dos silencios distintos no pueden decir lo mismo.

        «No hay datos» y «tus filtros no dejan pasar ninguno» llevan a
        acciones opuestas: esperar, o quitar un filtro.
        """
        respuesta = self.client.get(
            reverse("admin_explorador"), {"programa": "Inexistente"}
        )
        self.assertContains(respuesta, "Ningún estudiante encaja con estos filtros")
        self.assertNotContains(respuesta, "Todavía no hay nada que cruzar")
