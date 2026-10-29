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


class LeerPdfTest(TestCase):
    """Convertir un PDF de preguntas al formato del importador.

    Las pruebas no usan un PDF de verdad: construyen el texto que un PDF
    daría, que es lo que de verdad hay que convertir. Leer el archivo es
    trabajo de pypdf y no es lo que aquí se está probando.
    """

    def test_un_documento_numerado_sale_entero(self):
        from .importador import analizar
        from .lector_pdf import a_formato

        crudo = (
            "Encuesta de prueba\n"
            "1. ¿Cuál es la capital de Colombia?\n"
            "a. Medellín\n"
            "b. Bogotá\n"
            "c. Cali\n"
            "2. ¿Y la de Perú?\n"
            "a. Lima\n"
            "b. Quito\n"
            "c. La Paz\n"
        )
        texto, cuantas = a_formato(crudo)
        self.assertEqual(cuantas, 2)

        bloques = analizar(texto)
        self.assertEqual([b.enunciado for b in bloques][1], "¿Y la de Perú?")
        self.assertEqual(len(bloques[0].opciones), 3)

    def test_respeta_la_correcta_cuando_el_documento_la_marca(self):
        from .lector_pdf import a_formato

        crudo = (
            "1. ¿Capital de Colombia?\n"
            "a. Medellín\n"
            "b. Bogotá (correcta)\n"
            "c. Cali\n"
        )
        texto, _ = a_formato(crudo)
        self.assertIn("* Bogotá", texto)
        self.assertNotIn("(correcta)", texto)

    def test_entiende_la_respuesta_puesta_aparte(self):
        from .lector_pdf import a_formato

        crudo = (
            "1. ¿Capital de Colombia?\n"
            "a. Medellín\n"
            "b. Bogotá\n"
            "c. Cali\n"
            "Respuesta: b\n"
            "Explicación: es la capital desde 1819.\n"
        )
        texto, _ = a_formato(crudo)
        self.assertIn("* Bogotá", texto)
        self.assertIn("> es la capital desde 1819.", texto)

    def test_sin_respuesta_marcada_no_se_inventa(self):
        """Es el caso del cuadernillo: la clave va aparte, al final."""
        from .importador import analizar
        from .lector_pdf import a_formato

        crudo = "1. ¿Capital?\na. Medellín\nb. Bogotá\nc. Cali\n"
        texto, _ = a_formato(crudo)
        self.assertNotIn("*", texto)

        bloque = analizar(texto)[0]
        self.assertFalse(bloque.valida)
        # …y se arregla con el clic de la pantalla de revisión.
        self.assertTrue(analizar(texto, elegidas={1: 1})[0].valida)

    def test_las_opciones_repetidas_no_se_toman_por_encabezado(self):
        """Regresión: una escala Likert se repite en todas las preguntas.

        El primer filtro de mobiliario miraba solo si una línea se repetía, y
        se llevó por delante «Excelente / Bueno / Regular / Malo». De 23
        bloques quedaron 2. Ahora el mobiliario se reconoce por estar en el
        borde de la página, no por repetirse.
        """
        from .lector_pdf import a_formato

        paginas = []
        for i in range(1, 7):
            paginas.append(
                f"Encabezado del documento\n"
                f"{i}. Valora el punto {i}\n"
                "a. Excelente\nb. Bueno\nc. Regular\nd. Malo\n"
                "Página 1"
            )
        texto, cuantas = a_formato("\f".join(paginas))
        self.assertEqual(cuantas, 6)
        self.assertEqual(texto.count("- Excelente"), 6)
        self.assertNotIn("Encabezado del documento", texto)

    def test_la_portada_no_se_cose_al_primer_enunciado(self):
        """Regresión: la encuesta de usabilidad traía la portada pegada.

        Delante de la pregunta 1 va todo el frente del documento —título,
        instrucciones, enlace de descarga, cinco pasos de instalación— y se
        quedaba dentro del enunciado, donde recortarlo exigía cortar por la
        mitad de un párrafo. El número de la pregunta es la frontera que el
        propio documento pone: lo de delante va a «Contexto:», una línea que
        se borra entera si no servía.
        """
        from .importador import analizar
        from .lector_pdf import a_formato

        portada = (
            "Encuesta de usabilidad (prueba piloto). Responde con sinceridad: "
            "tus respuestas sirven para mejorar la aplicación. Paso 1: abre el "
            "enlace. Paso 2: instala el archivo descargado."
        )
        crudo = f"{portada} 1. Valora la instalación\na. Bueno\nb. Malo\n"
        texto, cuantas = a_formato(crudo)
        self.assertEqual(cuantas, 1)

        bloque = analizar(texto)[0]
        self.assertEqual(bloque.enunciado, "Valora la instalación")
        self.assertIn("Paso 2", bloque.contexto)

    def test_un_resto_corto_delante_del_numero_no_fabrica_contexto(self):
        """La otra cara: un número de página suelto no es un pasaje."""
        from .lector_pdf import a_formato

        texto, _ = a_formato("12 1. ¿Capital?\na. Cali\nb. Bogotá\n")
        self.assertNotIn("Contexto:", texto)

    def test_un_pdf_sin_texto_lo_dice_en_vez_de_callarse(self):
        from .lector_pdf import PdfIlegible, texto_de

        import io as _io
        with self.assertRaises(PdfIlegible):
            texto_de(_io.BytesIO(b"esto no es un pdf"))


class SubirUnPdfPorLaPantallaTest(TestCase):
    """La pantalla de importar, con un PDF de verdad por el formulario.

    Las de `LeerPdfTest` prueban el convertidor sin Django; estas prueban lo
    que la pantalla hace con el, que es donde estaban los dos fallos: un 500
    al leer sin nivel elegido, y el aviso de «elige el nivel» saltando cuando
    lo unico que se habia pedido era leer.
    """

    URL = "/admin/academics/question/importar/"
    SALTO = chr(10)

    def setUp(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser("jefe", "j@e.com", "z" * 24)
        self.client.login(username="jefe", password="z" * 24)

    @staticmethod
    def _un_pdf():
        """Un PDF de dos preguntas, armado a mano aqui mismo.

        Dos cosas que no se hacen y por que. **No se guarda un .pdf de apoyo
        en el repositorio**: una prueba que depende de un binario en el disco
        se cae el dia que alguien lo mueve, y lo que se prueba es la pantalla,
        no el archivo. **No se trae `reportlab`** solo para esto: son setecientos
        bytes de PDF escritos a mano —catalogo, pagina, flujo de texto y tabla
        de referencias— y no valen una dependencia nueva.
        """
        from io import BytesIO

        lineas = [
            "1. Cual es la capital de Colombia?",
            "a. Medellin",
            "b. Bogota",
            "2. Y la de Peru?",
            "a. Lima",
            "b. Quito",
        ]
        salto = "\n"
        flujo = ["BT", "/F1 12 Tf", "60 800 Td", "14 TL"]
        flujo += ["(" + l + ") Tj T*" for l in lineas]
        flujo.append("ET")
        contenido = salto.join(flujo).encode("latin-1")
        n = salto.encode()

        objetos = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            b"<< /Length " + str(len(contenido)).encode() + b" >>"
            + n + b"stream" + n + contenido + n + b"endstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        salida = bytearray(b"%PDF-1.4" + n)
        posiciones = []
        for i, cuerpo in enumerate(objetos, start=1):
            posiciones.append(len(salida))
            salida += str(i).encode() + b" 0 obj" + n + cuerpo + n + b"endobj" + n
        arranque = len(salida)
        salida += b"xref" + n + b"0 " + str(len(objetos) + 1).encode() + n
        salida += b"0000000000 65535 f " + n
        for pos in posiciones:
            salida += ("%010d 00000 n " % pos).encode() + n
        salida += (
            b"trailer" + n + b"<< /Size " + str(len(objetos) + 1).encode()
            + b" /Root 1 0 R >>" + n + b"startxref" + n
            + str(arranque).encode() + n + b"%%EOF" + n
        )
        archivo = BytesIO(bytes(salida))
        archivo.name = "preguntas.pdf"
        return archivo

    def test_leer_sin_elegir_nivel_no_revienta_ni_regania(self):
        r = self.client.post(self.URL, {"accion": "pdf", "pdf": self._un_pdf()})
        self.assertEqual(r.status_code, 200)
        html = r.content.decode("utf-8")
        self.assertIn("Bogota", html, "el cuadro tiene que quedar relleno")
        self.assertNotIn("Elige el nivel", html)

    def test_leer_no_guarda_nada_en_la_base(self):
        from .models import Question

        antes = Question.objects.count()
        self.client.post(self.URL, {"accion": "pdf", "pdf": self._un_pdf()})
        self.assertEqual(Question.objects.count(), antes)

    def test_revisar_sin_nivel_lo_pide_en_vez_de_caerse(self):
        suelto = self.SALTO.join(["Algo que no es nada", "- una", "- otra"])
        r = self.client.post(self.URL, {"accion": "revisar", "texto": suelto})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Elige el nivel", r.content.decode("utf-8"))
