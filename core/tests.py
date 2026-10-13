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


class VisitaGuiadaTest(TestCase):
    """Los primeros pasos se tachan al hacerse, no al pulsar «entendido»."""

    def setUp(self):
        self.usuario = get_user_model().objects.create_superuser(
            "nueva", "nueva@mail.udes.edu.co", "irrelevante-para-la-prueba"
        )
        self.client.force_login(self.usuario)

    def test_empieza_con_los_cuatro_pasos_pendientes(self):
        from .visita import estado

        v = estado(self.usuario)
        self.assertEqual(v["total"], 4)
        self.assertEqual(v["hechos"], 0)

    def test_abrir_el_explorador_tacha_su_paso(self):
        from .visita import PASO_EXPLORADOR, estado

        self.client.get(reverse("admin_explorador"))
        pasos = {p["clave"]: p["hecho"] for p in estado(self.usuario)["pasos"]}
        self.assertTrue(pasos[PASO_EXPLORADOR])

    def test_asomarse_al_importador_no_tacha_la_carga(self):
        """El paso dice «carga preguntas», no «asómate al importador»."""
        from .visita import PASO_CARGA, estado

        self.client.get(reverse("admin:academics_question_importar"))
        pasos = {p["clave"]: p["hecho"] for p in estado(self.usuario)["pasos"]}
        self.assertFalse(pasos[PASO_CARGA])

    def test_al_esconderla_deja_de_salir_y_se_puede_recuperar(self):
        from .visita import estado, se_puede_reabrir

        self.client.post(reverse("admin_visita"), {"accion": "cerrar"})
        self.assertIsNone(estado(self.usuario))
        self.assertTrue(se_puede_reabrir(self.usuario))

        self.client.post(reverse("admin_visita"), {"accion": "abrir"})
        self.assertIsNotNone(estado(self.usuario))
        self.assertFalse(se_puede_reabrir(self.usuario))

    def test_con_los_cuatro_hechos_desaparece_y_no_se_ofrece_recuperarla(self):
        """Una lista enteramente tachada deja de ser ayuda y pasa a ser ruido."""
        from .visita import ORDEN, estado, marcar, se_puede_reabrir

        for paso in ORDEN:
            marcar(self.usuario, paso)
        self.assertIsNone(estado(self.usuario))
        self.assertFalse(se_puede_reabrir(self.usuario))

    def test_cada_usuario_lleva_su_propia_cuenta(self):
        """Va en la base y por usuario, no en el navegador."""
        from .visita import PASO_EXPLORADOR, estado, marcar

        otra = get_user_model().objects.create_superuser(
            "otra", "otra@mail.udes.edu.co", "irrelevante-para-la-prueba"
        )
        marcar(self.usuario, PASO_EXPLORADOR)

        mios = {p["clave"]: p["hecho"] for p in estado(self.usuario)["pasos"]}
        suyos = {p["clave"]: p["hecho"] for p in estado(otra)["pasos"]}
        self.assertTrue(mios[PASO_EXPLORADOR])
        self.assertFalse(suyos[PASO_EXPLORADOR])


class RolesTest(TestCase):
    """Administrador y superadministrador: qué los separa, exactamente."""

    def setUp(self):
        from django.contrib.auth.models import Group

        from .roles import GRUPO_ADMIN, asegurar_roles

        asegurar_roles()
        U = get_user_model()

        self.jefe = U.objects.create_superuser(
            "jefe", "jefe@mail.udes.edu.co", "irrelevante-para-la-prueba"
        )
        self.admin = U.objects.create_user(
            "admin", "admin@mail.udes.edu.co", "irrelevante-para-la-prueba",
            is_staff=True,
        )
        self.admin.groups.add(Group.objects.get(name=GRUPO_ADMIN))

    def test_el_admin_trabaja_el_banco_de_preguntas(self):
        self.assertTrue(self.admin.has_perm("academics.add_question"))
        self.assertTrue(self.admin.has_perm("academics.change_question"))
        self.assertTrue(self.admin.has_perm("academics.view_question"))

    def test_el_admin_no_borra_nada(self):
        """Borrar una competencia se lleva sus niveles y sus preguntas detrás."""
        for permiso in ("academics.delete_competence", "academics.delete_level",
                        "academics.delete_question", "core.delete_studentreport"):
            self.assertFalse(self.admin.has_perm(permiso), permiso)

    def test_el_admin_no_gestiona_las_cuentas_del_panel(self):
        for permiso in ("auth.view_user", "auth.add_user", "auth.change_user",
                        "auth.delete_user", "auth.change_group"):
            self.assertFalse(self.admin.has_perm(permiso), permiso)

    def test_los_reportes_se_miran_pero_no_se_editan(self):
        """Editarlos a mano seria falsear la medicion."""
        self.assertTrue(self.admin.has_perm("core.view_studentreport"))
        self.assertFalse(self.admin.has_perm("core.change_studentreport"))

    def test_el_superadmin_lo_puede_todo(self):
        self.assertTrue(self.jefe.has_perm("auth.add_user"))
        self.assertTrue(self.jefe.has_perm("academics.delete_competence"))

    def test_el_admin_entra_al_panel_y_a_las_preguntas(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("admin:academics_question_changelist")).status_code,
            200,
        )

    def test_al_admin_las_cuentas_le_salen_como_no_disponible(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("admin:auth_user_changelist"))
        self.assertEqual(respuesta.status_code, 403)
        self.assertContains(respuesta, "No disponible", status_code=403)
        self.assertContains(
            respuesta, "solo para el superadministrador", status_code=403
        )

    def test_volver_a_correr_asegurar_roles_no_acumula_permisos(self):
        """Un grupo que solo crece acaba dando acceso que nadie concedio."""
        from django.contrib.auth.models import Group

        from .roles import GRUPO_ADMIN, asegurar_roles

        grupo = Group.objects.get(name=GRUPO_ADMIN)
        antes = grupo.permissions.count()
        asegurar_roles()
        asegurar_roles()
        self.assertEqual(Group.objects.get(name=GRUPO_ADMIN).permissions.count(), antes)


class AltaDeCuentasTest(TestCase):
    """Dar permisos es elegir un papel, no combinar cuarenta casillas."""

    def setUp(self):
        from .roles import asegurar_roles

        asegurar_roles()
        self.jefe = get_user_model().objects.create_superuser(
            "jefa", "jefa@mail.udes.edu.co", "irrelevante-para-la-prueba"
        )
        self.client.force_login(self.jefe)

    def _crear(self, usuario, papel):
        return self.client.post(
            reverse("admin:auth_user_add"),
            {
                "username": usuario,
                "password1": "una-clave-larga-de-prueba",
                "password2": "una-clave-larga-de-prueba",
                "papel": papel,
            },
            follow=True,
        )

    def test_elegir_administrador_deja_la_cuenta_lista(self):
        from django.contrib.auth.models import Group

        from .roles import GRUPO_ADMIN

        self._crear("nueva_admin", "admin")
        u = get_user_model().objects.get(username="nueva_admin")

        self.assertTrue(u.is_staff, "sin is_staff no puede ni entrar al panel")
        self.assertFalse(u.is_superuser)
        self.assertIn(Group.objects.get(name=GRUPO_ADMIN), u.groups.all())
        self.assertTrue(u.has_perm("academics.add_question"))
        self.assertFalse(u.has_perm("academics.delete_question"))
        self.assertFalse(u.has_perm("auth.add_user"))

    def test_elegir_superadministrador_no_deja_el_grupo_puesto(self):
        """Sus permisos no salen del grupo; dejarselo solo confundiria."""
        from django.contrib.auth.models import Group

        from .roles import GRUPO_ADMIN

        self._crear("nueva_jefa", "super")
        u = get_user_model().objects.get(username="nueva_jefa")

        self.assertTrue(u.is_superuser)
        self.assertNotIn(Group.objects.get(name=GRUPO_ADMIN), u.groups.all())
        self.assertTrue(u.has_perm("auth.add_user"))

    def test_sin_acceso_crea_la_cuenta_pero_no_la_deja_entrar(self):
        self._crear("sin_panel", "ninguno")
        u = get_user_model().objects.get(username="sin_panel")
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)

    def test_el_formulario_no_pide_permisos_sueltos(self):
        respuesta = self.client.get(reverse("admin:auth_user_add"))
        self.assertContains(respuesta, "papel")
        self.assertNotContains(respuesta, "user_permissions")

    def test_nadie_se_quita_a_si_mismo_el_acceso(self):
        """Es la unica forma de dejar el panel sin superadministrador."""
        respuesta = self.client.post(
            reverse("admin:auth_user_change", args=[self.jefe.pk]),
            {
                "username": self.jefe.username,
                "first_name": "", "last_name": "", "email": self.jefe.email,
                "papel": "ninguno",
                "is_active": "on",
                "last_login_0": "", "last_login_1": "",
                "date_joined_0": "2026-10-13", "date_joined_1": "10:00:00",
            },
            follow=True,
        )
        self.jefe.refresh_from_db()
        self.assertTrue(self.jefe.is_superuser, "se quedo sin acceso a su propio panel")
        self.assertContains(respuesta, "No puedes cambiar tu propio papel")

    def test_los_permisos_se_leen_en_espanol(self):
        from django.contrib.auth.models import Permission

        from .roles import traducir_permisos

        traducir_permisos()
        nombres = list(
            Permission.objects.filter(
                content_type__app_label__in=["academics", "auth"]
            ).values_list("name", flat=True)
        )
        self.assertTrue(nombres)
        for nombre in nombres:
            self.assertFalse(nombre.startswith("Can "), nombre)
        self.assertIn("Puede añadir competencia", nombres)
        self.assertIn("Puede añadir grupo", nombres)
