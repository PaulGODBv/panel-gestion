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


class NormalizarIconoTest(TestCase):
    """Un archivo cualquiera, convertido en el PNG que espera la app.

    No usa la base: `iconos` no importa Django, igual que `importador` y
    `lector_pdf`.
    """

    @staticmethod
    def _imagen(ancho, alto, color=(200, 30, 30, 255), fondo=(0, 0, 0, 0), margen=0):
        from PIL import Image

        im = Image.new("RGBA", (ancho, alto), fondo)
        for y in range(margen, alto - margen):
            for x in range(margen, ancho - margen):
                im.putpixel((x, y), color)
        return im

    @staticmethod
    def _bytes(im, formato="PNG"):
        import io as _io

        buf = _io.BytesIO()
        if formato == "JPEG":
            im = im.convert("RGB")
        im.save(buf, format=formato)
        return buf.getvalue()

    def test_sale_cuadrado_del_lado_pedido(self):
        from .iconos import LADO, normalizar
        from PIL import Image
        import io as _io

        png = normalizar(self._bytes(self._imagen(400, 150)))
        salida = Image.open(_io.BytesIO(png))
        self.assertEqual((LADO, LADO), salida.size)
        self.assertEqual("PNG", salida.format)
        self.assertEqual("RGBA", salida.mode)

    def test_dos_originales_distintos_acaban_ocupando_lo_mismo(self):
        """Es la razón de ser del módulo.

        Uno sube el dibujo recortado al ras y otro con medio folio de margen.
        Sin normalizar, en la lista de niveles uno se ve enorme y el otro
        flotando. Recortando al contenido y devolviendo siempre el mismo aire,
        los dos ocupan igual.
        """
        from .iconos import normalizar
        from PIL import Image
        import io as _io

        al_ras = normalizar(self._bytes(self._imagen(100, 100)))
        con_aire = normalizar(self._bytes(self._imagen(300, 300, margen=100)))

        caja_a = Image.open(_io.BytesIO(al_ras)).getbbox()
        caja_b = Image.open(_io.BytesIO(con_aire)).getbbox()
        self.assertEqual(caja_a, caja_b)

    def test_no_deforma_lo_que_no_es_cuadrado(self):
        from .iconos import normalizar
        from PIL import Image
        import io as _io

        png = normalizar(self._bytes(self._imagen(400, 100)))
        caja = Image.open(_io.BytesIO(png)).getbbox()
        ancho, alto = caja[2] - caja[0], caja[3] - caja[1]
        # El original es cuatro veces más ancho que alto; tiene que seguir
        # siéndolo, centrado, y no estirado hasta el cuadrado.
        self.assertAlmostEqual(4.0, ancho / alto, delta=0.15)

    def test_el_fondo_blanco_de_un_jpg_se_quita(self):
        """Un JPG no tiene transparencia y su blanco se vería como un cuadro."""
        from .iconos import normalizar
        from PIL import Image
        import io as _io

        original = self._imagen(200, 200, fondo=(255, 255, 255, 255), margen=50)
        png = normalizar(self._bytes(original, formato="JPEG"))
        salida = Image.open(_io.BytesIO(png))
        self.assertEqual(0, salida.getpixel((2, 2))[3], "la esquina tiene que quedar transparente")

    def test_lo_que_no_es_una_imagen_lo_dice(self):
        from .iconos import IconoInvalido, normalizar

        with self.assertRaises(IconoInvalido):
            normalizar(b"esto no es una imagen")
        with self.assertRaises(IconoInvalido):
            normalizar(b"")

    def test_una_imagen_en_blanco_no_pasa(self):
        from .iconos import IconoInvalido, normalizar

        vacia = self._imagen(100, 100, color=(0, 0, 0, 0))
        with self.assertRaises(IconoInvalido):
            normalizar(self._bytes(vacia))


class IconoDeNivelPorLaApiTest(TestCase):
    """El camino entero: se sube, se sirve, y la app recibe su URL."""

    def setUp(self):
        from django.test import override_settings
        from .models import Competence, Level

        self.competencia = Competence.objects.create(name="Lectura", description="", order=1)
        self.nivel = Level.objects.create(
            competence=self.competencia, name="Nivel 1", description="", order=1
        )

    @staticmethod
    def _png():
        from PIL import Image
        import io as _io

        im = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        for y in range(20, 100):
            for x in range(20, 100):
                im.putpixel((x, y), (10, 90, 160, 255))
        buf = _io.BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue()

    def test_un_nivel_sin_icono_no_lo_anuncia(self):
        from .serializers import LevelSummarySerializer

        datos = LevelSummarySerializer(self.nivel).data
        self.assertIsNone(datos["icono_url"], "sin icono, la app no debe pedir nada")

    def test_al_subirlo_la_api_da_su_url_y_la_url_lo_sirve(self):
        from django.contrib.auth import get_user_model
        from .iconos import normalizar
        from .serializers import LevelSummarySerializer

        self.nivel.icono = normalizar(self._png())
        self.nivel.icono_version = 1
        self.nivel.save()

        datos = LevelSummarySerializer(self.nivel).data
        self.assertEqual(f"/api/levels/{self.nivel.pk}/icono/1/", datos["icono_url"])

        get_user_model().objects.create_superuser("jefa", "j@e.com", "x" * 24)
        self.client.login(username="jefa", password="x" * 24)
        r = self.client.get(datos["icono_url"])
        self.assertEqual(200, r.status_code)
        self.assertEqual("image/png", r["Content-Type"])
        self.assertIn("immutable", r["Cache-Control"])
        # Los cuatro bytes con los que empieza todo PNG.
        self.assertTrue(r.content.startswith(bytes([137, 80, 78, 71])))

    def test_la_url_que_recibe_la_app_es_absoluta(self):
        """Regresión: salía relativa y el teléfono no sabría contra qué host resolverla.

        Es el mismo tropiezo que ya estaba documentado para la imagen de
        contexto, y se repitió aquí porque `CompetenceListView` serializaba
        sin pasar la petición en el contexto.
        """
        from django.test import override_settings
        from .iconos import normalizar

        self.nivel.icono = normalizar(self._png())
        self.nivel.icono_version = 3
        self.nivel.save()

        # Con la cabecera y no con sesion: `/api/competences/` es el
        # endpoint de la app, y se prueba como la app lo llama.
        with override_settings(RETA2_API_KEY="clave-de-esta-prueba"):
            r = self.client.get(
                "/api/competences/", headers={"x-api-key": "clave-de-esta-prueba"}
            )
        self.assertEqual(200, r.status_code)

        urls = [n["icono_url"] for c in r.json() for n in c["levels"] if n["icono_url"]]
        self.assertEqual(1, len(urls))
        self.assertTrue(
            urls[0].startswith("http://"),
            f"tiene que traer host, y vino «{urls[0]}»",
        )
        self.assertTrue(urls[0].endswith(f"/api/levels/{self.nivel.pk}/icono/3/"))

    def test_la_version_cambia_con_cada_icono_nuevo(self):
        """Sin esto, la cache de un anio serviria el icono viejo durante dias."""
        from .admin import FormularioDeNivel
        from django.core.files.uploadedfile import SimpleUploadedFile

        def sube():
            formulario = FormularioDeNivel(
                data={
                    "competence": self.competencia.pk,
                    "name": self.nivel.name,
                    "description": "x",
                    "order": self.nivel.order,
                    "formato_practica": "opcion",
                },
                files={
                    "archivo_de_icono": SimpleUploadedFile(
                        "i.png", self._png(), content_type="image/png"
                    )
                },
                instance=self.nivel,
            )
            self.assertTrue(formulario.is_valid(), formulario.errors)
            return formulario.save()

        primero = sube()
        self.assertEqual(1, primero.icono_version)
        segundo = sube()
        self.assertEqual(2, segundo.icono_version, "subir otro tiene que invalidar la URL")

    def test_un_archivo_que_no_sirve_sale_como_error_del_formulario(self):
        from .admin import FormularioDeNivel
        from django.core.files.uploadedfile import SimpleUploadedFile

        formulario = FormularioDeNivel(
            data={
                "competence": self.competencia.pk,
                "name": self.nivel.name,
                "description": "x",
                "order": self.nivel.order,
                "formato_practica": "opcion",
            },
            files={
                "archivo_de_icono": SimpleUploadedFile(
                    "i.png", b"no soy una imagen", content_type="image/png"
                )
            },
            instance=self.nivel,
        )
        self.assertFalse(formulario.is_valid())
        self.assertIn("archivo_de_icono", formulario.errors)

    def test_pedir_el_icono_de_un_nivel_que_no_lo_tiene_da_404(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser("jefa", "j@e.com", "x" * 24)
        self.client.login(username="jefa", password="x" * 24)
        r = self.client.get(f"/api/levels/{self.nivel.pk}/icono/0/")
        self.assertEqual(404, r.status_code)
