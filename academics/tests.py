from django.test import TestCase

# Create your tests here.


class ElegirLaCorrectaAManoTest(TestCase):
    """Marcar la correcta en la revisión, sin asterisco en el texto.

    Viene de ver a un profesor cargar preguntas: pega un cuestionario tal como
    viene —de una cartilla, de un Word— donde la respuesta buena no está
    marcada en ninguna parte, y el importador se lo rechazaba entero.

    No usa la base de datos: el analizador no importa Django a propósito.
    """

    TEXTO = (
        "¿Cuál es el mecanismo para reformar la Constitución?\n"
        "- El plebiscito\n"
        "- El referendo constitucional\n"
        "- La consulta popular\n"
    )

    def test_sin_asterisco_el_bloque_no_entra(self):
        from .importador import analizar

        bloque = analizar(self.TEXTO)[0]
        self.assertFalse(bloque.valida)
        self.assertTrue(
            any("«*»" in p for p in bloque.problemas),
            "el problema tiene que decir que falta la marca",
        )

    def test_eligiendo_la_correcta_el_bloque_queda_listo(self):
        from .importador import analizar

        bloque = analizar(self.TEXTO, elegidas={1: 1})[0]
        self.assertTrue(bloque.valida, bloque.problemas)
        correctas = [o.texto for o in bloque.opciones if o.correcta]
        self.assertEqual(correctas, ["El referendo constitucional"])

    def test_lo_elegido_pisa_el_asterisco_del_texto(self):
        """Si las dos cosas se contradicen, manda el clic.

        Es lo que uno espera: el asterisco se escribió antes, el clic es la
        corrección que se acaba de hacer mirando la pantalla.
        """
        from .importador import analizar

        con_marca = self.TEXTO.replace("- El plebiscito", "* El plebiscito")
        bloque = analizar(con_marca, elegidas={1: 2})[0]
        correctas = [o.texto for o in bloque.opciones if o.correcta]
        self.assertEqual(correctas, ["La consulta popular"])

    def test_una_eleccion_fuera_de_rango_se_ignora(self):
        """Un número que no corresponde a ninguna opción no rompe nada."""
        from .importador import analizar

        con_marca = self.TEXTO.replace("- El plebiscito", "* El plebiscito")
        bloque = analizar(con_marca, elegidas={1: 99})[0]
        correctas = [o.texto for o in bloque.opciones if o.correcta]
        self.assertEqual(correctas, ["El plebiscito"])
