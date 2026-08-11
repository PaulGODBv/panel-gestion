from django.core.management.base import BaseCommand
from academics.models import Competence, Level, Question, QuestionOption


class Command(BaseCommand):
    help = 'Poblar la base de datos con las preguntas iniciales de Reta2'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚀 Iniciando población de datos...')

        # Limpiar datos existentes
        QuestionOption.objects.all().delete()
        Question.objects.all().delete()
        Level.objects.all().delete()
        Competence.objects.all().delete()

        self.stdout.write('🗑️  Datos anteriores eliminados')

        # ── COMPETENCIAS ──────────────────────────────────────────
        lectura = Competence.objects.create(
            name='Lectura Crítica',
            description='Desarrolla habilidades para analizar, interpretar y evaluar textos de manera crítica',
            order=1
        )
        razonamiento = Competence.objects.create(
            name='Razonamiento Cuantitativo',
            description='Capacidad para comprender, analizar y resolver problemas que involucran información cuantitativa',
            order=2
        )
        ingles = Competence.objects.create(
            name='Inglés',
            description='Desarrolla habilidades en comprensión, gramática y vocabulario en inglés',
            order=3
        )
        ciudadanas = Competence.objects.create(
            name='Competencias Ciudadanas',
            description='Desarrolla habilidades para la participación ciudadana responsable',
            order=4
        )

        self.stdout.write('✅ Competencias creadas')

        # ── NIVELES ───────────────────────────────────────────────
        # Lectura Crítica
        lc_basico = Level.objects.create(
            competence=lectura,
            name='Nivel 1 – Comprensión literal',
            description='Identifica información explícita en textos',
            order=1
        )
        lc_intermedio = Level.objects.create(
            competence=lectura,
            name='Nivel 2 – Interpretación e inferencia',
            description='Identifica la organización y estructura de textos',
            order=2,
            is_Locked_by_default=True
        )
        lc_avanzado = Level.objects.create(
            competence=lectura,
            name='Nivel 3 – Análisis crítico y evaluación',
            description='Evalúa la calidad y credibilidad de textos',
            order=3,
            is_Locked_by_default=True
        )

        # Razonamiento Cuantitativo
        rq_basico = Level.objects.create(
            competence=razonamiento,
            name='Interpretación',
            description='Comprende y transforma la información cuantitativa',
            order=1
        )
        rq_intermedio = Level.objects.create(
            competence=razonamiento,
            name='Argumentación',
            description='Valida procedimientos y estrategias matemáticas',
            order=2,
            is_Locked_by_default=True
        )
        rq_avanzado = Level.objects.create(
            competence=razonamiento,
            name='Formulación y ejecución',
            description='Plantea e implementa estrategias cuantitativas',
            order=3,
            is_Locked_by_default=True
        )

        # Inglés
        ing_feelings = Level.objects.create(
            competence=ingles,
            name='Feelings',
            description='Identifica emociones y sentimientos en inglés',
            order=1
        )
        ing_conversations = Level.objects.create(
            competence=ingles,
            name='Complete the Conversations',
            description='Completa conversaciones cotidianas en inglés',
            order=2,
            is_Locked_by_default=True
        )
        ing_text = Level.objects.create(
            competence=ingles,
            name='Complete the text',
            description='Completa textos con la palabra correcta',
            order=3,
            is_Locked_by_default=True
        )
        ing_reading = Level.objects.create(
            competence=ingles,
            name='Reading Comprehension',
            description='Comprensión lectora avanzada en inglés',
            order=4,
            is_Locked_by_default=True
        )

        # Competencias Ciudadanas
        cc_basico = Level.objects.create(
            competence=ciudadanas,
            name='Nivel 1 – Conocimiento Constitucional',
            description='Conoce los derechos y deberes fundamentales',
            order=1
        )
        cc_intermedio = Level.objects.create(
            competence=ciudadanas,
            name='Nivel 2 – Análisis de Perspectivas',
            description='Reconoce diferentes perspectivas sociales',
            order=2,
            is_Locked_by_default=True
        )
        cc_avanzado = Level.objects.create(
            competence=ciudadanas,
            name='Nivel 3 – Análisis Crítico',
            description='Analiza y evalúa argumentos y discursos',
            order=3,
            is_Locked_by_default=True
        )

        self.stdout.write('✅ Niveles creados')

        # ── PREGUNTAS ─────────────────────────────────────────────
        # Helper para crear pregunta + opciones
        def create_question(level, text, options, correct_order,
                            explanation='', reading_text='', context_image=''):
            q = Question.objects.create(
                level=level,
                text=text,
                correct_option_order=correct_order,
                explanation=explanation,
                reading_text=reading_text,
                context_image=context_image
            )
            for i, option_text in enumerate(options, start=1):
                QuestionOption.objects.create(
                    question=q,
                    text=option_text,
                    order=i
                )
            return q

        READING_MEDICINA = (
            "La medicina popular colombiana conserva una amplia serie de conocimientos "
            "empíricos sobre gran diversidad de recursos botánicos, que han sido esenciales "
            "para el cuidado de la salud. Pero, con la oficialización de la medicina a finales "
            "del siglo XIX, la creación de las primeras escuelas de medicina y de farmacia y la "
            "creación de una legislación que buscaba regular estas disciplinas, muchos de estos "
            "conocimientos fueron rechazados al igual que sus prácticas médicas.\n\n"
            "Paradójicamente, mientras la medicina oficial negaba los conocimientos populares, "
            "se servía de ellos para desarrollar muchos de los avances farmacéuticos de los que "
            "se vale la medicina oficial para sus tratamientos.\n\n"
            "Por otro lado, según la Organización Mundial de la Salud, la atención primaria en "
            "salud por parte de la medicina oficial cubre apenas a un 20% de la población en los "
            "países en vías de desarrollo, mientras que el 80% tiene que recurrir a otras "
            "prácticas médicas populares y lo hace en gran parte por la poca garantía de acceso "
            "y de aseguramiento de la población pobre."
        )

        READING_TRUMAN = (
            "En su discurso de posesión como presidente de Estados Unidos el 20 de enero de 1949, "
            "Harry Truman anunció al mundo entero su concepto de 'trato justo'.\n\n"
            "La doctrina Truman inició una nueva era en la comprensión y el manejo de los asuntos "
            "mundiales, en particular de aquellos que se referían a los países económicamente menos "
            "avanzados.\n\nEl propósito era bastante ambicioso: crear las condiciones necesarias "
            "para reproducir en todo el mundo los rasgos característicos de las sociedades avanzadas "
            "de la época: altos niveles de industrialización y urbanización, tecnificación de la "
            "agricultura, rápido crecimiento de la producción material y de los niveles de vida, y "
            "adopción generalizada de la educación y los valores culturales modernos.\n\n"
            "Producir más es la clave para la paz y la prosperidad. Y la clave para producir más "
            "es una aplicación mayor y más vigorosa del conocimiento técnico y científico moderno."
        )

        READING_BICICLETA = (
            "Recientemente, Isabel se convirtió en madrastra de Felipe. Ella acaba de estrellar "
            "accidentalmente la bicicleta de Felipe porque él la dejó a la entrada del garaje.\n\n"
            "Felipe: Te anotaste un punto. ¡Gracias por dejarme sin bicicleta!\n"
            "Isabel: ¿Y cómo querías que la viera?\n"
            "Felipe: ¡Pues usando el espejo retrovisor, así se hace!\n"
            "Isabel: Perdón, pero escuché a tu padre decirte que dejaras tu bicicleta lejos.\n"
            "Felipe: Ah. (Se desploma en una silla.)\n"
            "Padre: En primer lugar, no le digas a Isabel 'ella'. Eso es muy grosero. "
            "En segundo lugar, te he dicho que no dejes tu bicicleta a la entrada del garaje."
        )

        READING_ARBOL = (
            "El siguiente pasaje es tomado de una novela ambientada en la década de 1930. "
            "David y su esposa, Helena, han estado viviendo en una urbanización nueva, La Arboleda.\n\n"
            "Cuando regresé a La Arboleda descargué el pequeño árbol a la entrada cerca de la "
            "puerta principal. Helena dijo: 'David, ¿dónde diablos has estado?'\n"
            "'Me fui y compré un árbol', le dije.\n"
            "Su expresión cambió cuando lo vio, y tengo que admitir que se veía más bien sucio, "
            "débil y gris, con sus raíces apretadas como un nudo de estopa mojada sin forma.\n"
            "'Sí, pero ¿qué es?', preguntó ella.\n"
            "'Es un árbol de caucho. Caucho de azúcar.'\n"
            "Helena: 'Honestamente prefiero algo decorativo, especialmente para allá, justo en "
            "el frente de la casa; algo como arbustos con buena floración, o camelias, o celindas.'"
        )

        READING_JUSTICIA = (
            "La Justicia es, en primer lugar, una cualidad posible, pero no necesaria, de un orden "
            "social que regula las relaciones mutuas entre los hombres.\n\n"
            "Solo secundariamente es una virtud humana, ya que un hombre es justo solo si su "
            "conducta se adecúa a las normas de un orden social supuestamente justo.\n\n"
            "La búsqueda de la Justicia es la eterna búsqueda de la felicidad humana. Es una "
            "finalidad que el hombre no puede encontrar por sí mismo y, por ello, la busca en "
            "la sociedad. La Justicia es la felicidad social, garantizada por un orden social.\n\n"
            "Platón, identificando la Justicia con la felicidad, sostiene que un hombre justo "
            "es feliz y un hombre injusto es infeliz.\n\n"
            "- Kelsen, H. (1992). ¿Qué es justicia?"
        )

        READING_HOBBES = (
            "Aunque las comodidades de esta vida pueden aumentarse con la ayuda mutua, sin embargo, "
            "como eso se puede conseguir dominando a los demás mejor que asociándose con ellos, "
            "nadie debe dudar de que los hombres, por su naturaleza, si no existiera el miedo, "
            "se verían inclinados más al dominio que a la sociedad.\n\n"
            "Por lo tanto, hay que afirmar que el origen de las sociedades grandes y duraderas no "
            "se ha debido a la mutua benevolencia de los hombres, sino al miedo mutuo.\n\n"
            "- Hobbes, T. (1999). Tratado sobre el ciudadano."
        )

        # ── LECTURA CRÍTICA - BÁSICO ──────────────────────────────
        create_question(
            level=lc_basico,
            text="Según el texto, para que la atención primaria en salud pueda atender a más del "
                 "20% de la población, sería necesario principalmente:",
            options=[
                "Promover sistemas de financiación adecuados y equitativos.",
                "Prever el envejecimiento demográfico de la población.",
                "Respetar el derecho a los servicios de salud y las diferencias culturales.",
                "Crear un sistema de información con enfoque de Derechos Humanos."
            ],
            correct_order=1,
            explanation="El texto indica que la medicina oficial cubre apenas al 20% de la "
                        "población debido a problemas de acceso y aseguramiento.",
            reading_text=READING_MEDICINA
        )
        create_question(
            level=lc_basico,
            text="Para alcanzar los propósitos de la doctrina, Harry Truman proponía como estrategia:",
            options=[
                "Elevar los niveles de industrialización y urbanización.",
                "Tratar equitativamente a todas las naciones y pueblos del planeta.",
                "Producir más fortaleciendo la alianza entre capital, ciencia y tecnología.",
                "Mitigar las condiciones de pobreza, hambre y miseria en todas las áreas del globo."
            ],
            correct_order=3,
            explanation="Truman propone que la clave para producir más es una aplicación mayor "
                        "del conocimiento técnico y científico moderno.",
            reading_text=READING_TRUMAN
        )
        create_question(
            level=lc_basico,
            text="De acuerdo con Arturo Escobar, el propósito de la doctrina Truman era:",
            options=[
                "Crear condiciones para reproducir en todo el mundo los rasgos de las sociedades avanzadas.",
                "Adoptar en el primer mundo el sueño americano de paz y abundancia.",
                "Iniciar una nueva era en la comprensión de los países más avanzados.",
                "Generar altos niveles de industrialización en los países desarrollados."
            ],
            correct_order=1,
            explanation="El texto indica que la doctrina Truman inició una nueva era en la "
                        "comprensión y el manejo de los asuntos mundiales.",
            reading_text=READING_TRUMAN
        )
        create_question(
            level=lc_basico,
            text="La bicicleta averiada le da a Felipe una oportunidad de:",
            options=[
                "Insultar a su padre.",
                "Buscar el apoyo de su padre.",
                "Mostrar su resentimiento contra Isabel.",
                "Demostrarle a Isabel que él es casi un adulto."
            ],
            correct_order=3,
            explanation="Felipe usa el incidente para expresar su resentimiento contra Isabel.",
            reading_text=READING_BICICLETA
        )
        create_question(
            level=lc_basico,
            text="Helena cambió su expresión porque:",
            options=[
                "David compró un árbol.",
                "El árbol le pareció costoso.",
                "El árbol no tenía la mejor apariencia.",
                "David quería sembrar el árbol en el jardín."
            ],
            correct_order=3,
            explanation="El texto describe que el árbol se veía sucio, débil y gris.",
            reading_text=READING_ARBOL
        )
        create_question(
            level=lc_basico,
            text="Cuando Helena está discutiendo con David, ella:",
            options=[
                "Enfatiza sus puntos de vista.",
                "Indaga por los intereses del otro.",
                "Se concentra en la búsqueda de un acuerdo.",
                "Convierte la discusión en un ataque personal."
            ],
            correct_order=1,
            explanation="Helena enfatiza sus preferencias estéticas y critica la elección de David.",
            reading_text=READING_ARBOL
        )

        # ── LECTURA CRÍTICA - INTERMEDIO ──────────────────────────
        create_question(
            level=lc_intermedio,
            text="La promoción de estudios académicos para determinar cuáles prácticas de la "
                 "medicina popular son perjudiciales implica que:",
            options=[
                "Se prolongue la inconformidad de quienes practican la medicina oficial.",
                "Se inicien procesos de regulación oficiales sobre este tipo de prácticas.",
                "Se derogue la ley de que la medicina científica es la única oficial.",
                "Se extienda la brecha entre la medicina química y la botánica."
            ],
            correct_order=2,
            explanation="Estudiar las prácticas populares llevaría a determinar cuáles son "
                        "beneficiosas y cuáles perjudiciales, lo que implicaría regulación.",
            reading_text=READING_MEDICINA
        )
        create_question(
            level=lc_intermedio,
            text="De los siguientes enunciados, ¿cuál NO se puede deducir de la afirmación "
                 "'un hombre es justo solo si su conducta se adecúa a las normas de un orden "
                 "social supuestamente justo'?",
            options=[
                "Un hombre que se comporta justamente sigue las normas de un orden social.",
                "Todo hombre que no se adecúe a las normas de un orden social justo es injusto.",
                "Hay hombres que se adecúan a un orden social justo y sin embargo son injustos.",
                "No hay hombres que se adecúen a un orden social justo y sean injustos."
            ],
            correct_order=3,
            explanation="Según la afirmación, si un hombre se adecúa a las normas de un orden "
                        "social justo, entonces es justo. No puede ser injusto.",
            reading_text=READING_JUSTICIA
        )
        create_question(
            level=lc_intermedio,
            text="Según el enunciado 'La búsqueda de la Justicia es la eterna búsqueda de la "
                 "felicidad humana', ¿cuál de las siguientes opciones se puede concluir?",
            options=[
                "Quien busca la justicia no encuentra la felicidad.",
                "Quien busca la justicia también busca la felicidad.",
                "El que busca la justicia nunca encuentra la felicidad.",
                "El que busca la justicia siempre encuentra la felicidad."
            ],
            correct_order=2,
            explanation="Si la búsqueda de la justicia es la búsqueda de la felicidad, "
                        "entonces quien busca justicia también busca felicidad.",
            reading_text=READING_JUSTICIA
        )
        create_question(
            level=lc_intermedio,
            text="¿Qué función cumple el conector 'sin embargo' en el texto de Hobbes?",
            options=[
                "Aclarar la idea de que la ayuda mutua aumenta las comodidades.",
                "Desmentir la idea de que la ayuda mutua aumenta las comodidades.",
                "Contrastar la idea de que la ayuda mutua aumenta las comodidades con la idea "
                "de que es más efectivo dominar a los demás.",
                "Cuestionar la idea de que la ayuda mutua aumenta las comodidades."
            ],
            correct_order=3,
            explanation="'Sin embargo' establece un contraste entre la ayuda mutua y el dominio.",
            reading_text=READING_HOBBES
        )
        create_question(
            level=lc_intermedio,
            text="Por un lado, el autor afirma que el miedo origina las sociedades. Por otro lado, "
                 "que si no existiera el miedo, el hombre buscaría dominar a los demás. "
                 "¿Cuál es la relación argumentativa entre estas dos afirmaciones?",
            options=[
                "La primera es una premisa y la segunda la conclusión.",
                "La segunda es una premisa y la primera la conclusión.",
                "Las dos son premisas de un mismo argumento.",
                "Las dos presentan la misma conclusión de diferente manera."
            ],
            correct_order=3,
            explanation="Ambas afirmaciones son premisas que sustentan la conclusión de que "
                        "el origen de las sociedades se debe al miedo mutuo.",
            reading_text=READING_HOBBES
        )

        # ── LECTURA CRÍTICA - AVANZADO ────────────────────────────
        create_question(
            level=lc_avanzado,
            text="¿Cuál de las siguientes afirmaciones expresa de manera exacta la antítesis "
                 "de la tesis principal del texto de Hobbes?",
            options=[
                "El origen de las sociedades se debe a la desconfianza de los hombres.",
                "El origen de las sociedades se explica por la indiferencia de los hombres.",
                "El origen de las sociedades se halla en la obediencia recíproca de los hombres.",
                "El origen de las sociedades resulta de la colaboración desinteresada de los hombres."
            ],
            correct_order=4,
            explanation="La tesis de Hobbes es que las sociedades se originan por el miedo "
                        "mutuo, no por la benevolencia. La antítesis sería la colaboración desinteresada.",
            reading_text=READING_HOBBES
        )
        create_question(
            level=lc_avanzado,
            text="De acuerdo con el texto de Hobbes, ¿por qué aparecieron sociedades grandes y duraderas?",
            options=[
                "Es natural para el hombre asociarse con otros para ejercer su dominio.",
                "Para ampliar su capacidad de dominio, al hombre le resulta más efectivo vivir en sociedad.",
                "Es propio del hombre evitar todo tipo de dominio a través de relaciones confiables.",
                "El hombre busca seguridad y es más seguro vivir en comunidad que estar expuesto "
                "a ser dominado por otro."
            ],
            correct_order=4,
            explanation="Según Hobbes, el hombre forma sociedades por miedo mutuo, buscando "
                        "seguridad ante la posibilidad de ser dominado.",
            reading_text=READING_HOBBES
        )
        create_question(
            level=lc_avanzado,
            text="La afirmación de Luisa 'Si estoy con un man que me gusta porque sí, "
                 "¿por qué no voy a estar con otro por plata?' implica que ella:",
            options=[
                "Toma decisiones dentro de las normas de una comunidad.",
                "No le da más importancia a los sentimientos que al dinero.",
                "Gusta de los hombres que tienen dinero.",
                "Cree que la opinión de los demás es importante a la hora de decidir."
            ],
            correct_order=2,
            explanation="Luisa equipara las relaciones por gusto con las relaciones por dinero, "
                        "sugiriendo que no hay diferencia moral entre ambas.",
            reading_text=""
        )

        self.stdout.write('✅ Preguntas de Lectura Crítica creadas')

        # ── RAZONAMIENTO CUANTITATIVO - BÁSICO ───────────────────
        READING_SISMOS = (
            "La tabla muestra el total de sismos registrados en el planeta durante la primera "
            "década del siglo XXI y la distribución de aquellos con magnitud mayor a 5,0.\n\n"
            "Los datos muestran que a mayor magnitud, menor es la cantidad de sismos registrados. "
            "El promedio anual de sismos en la primera década fue de 3.783."
        )

        create_question(
            level=rq_basico,
            text="Un sismólogo afirma que en cualquier año era más probable que hubiese sismos "
                 "de baja que de alta magnitud. La relación que justifica esta opinión es:",
            options=[
                "A mayor magnitud, mayor cantidad de sismos.",
                "A mayor magnitud, menor cantidad de sismos.",
                "A mayor cantidad de sismos, menor magnitud de estos.",
                "A mayor cantidad de sismos, mayor magnitud de estos."
            ],
            correct_order=2,
            explanation="La tabla muestra que a mayor magnitud, menor cantidad de sismos registrados.",
            reading_text=READING_SISMOS,
            context_image="imagen_sismos"
        )
        create_question(
            level=rq_basico,
            text="¿Cuál de los siguientes cocientes permite estimar la cantidad de sismos mensuales?",
            options=[
                "Total de sismos sobre meses del año.",
                "Total de sismos por año sobre meses del año.",
                "Total de sismos por año sobre días del año.",
                "Total de sismos sobre su magnitud."
            ],
            correct_order=2,
            explanation="Para estimar sismos mensuales se divide el total anual entre 12 meses.",
            reading_text=READING_SISMOS,
            context_image="imagen_sismos"
        )
        create_question(
            level=rq_basico,
            text="En la primera década del siglo XXI, la proporción de sismos de magnitud "
                 "entre 8,0 y 8,9 es de, aproximadamente:",
            options=[
                "1 de cada 3.000 sismos.",
                "1 de cada 12 sismos.",
                "12 de cada 18.000 sismos.",
                "12 de cada 4.000 sismos."
            ],
            correct_order=1,
            explanation="Sismos de magnitud 8,0-8,9: 12. Total: 37.830. Proporción: 12/37.830 ≈ 1/3.000.",
            reading_text=READING_SISMOS,
            context_image="imagen_sismos"
        )

        READING_PILATES = (
            "Un instructor de pilates tiene un estudio con los equipos necesarios para que una "
            "persona reciba entrenamiento personalizado. La tabla muestra la cantidad de sesiones "
            "por semana, el total en el mes y el costo mensual que una persona tendría que pagar."
        )

        create_question(
            level=rq_basico,
            text="Camilo quiere inscribirse a clases de pilates y escoger el total de sesiones "
                 "mensual donde el costo por sesión sea menor. Camilo elige 2 sesiones por semana. "
                 "¿Logra su propósito?",
            options=[
                "No, pues el costo por sesión menor lo obtiene si toma 4 sesiones por semana.",
                "Sí, pues tomar 2 sesiones por semana tiene el menor costo mensual.",
                "No, pues se paga un menor precio por sesión si toma 3 sesiones por semana.",
                "Sí, pues tomar menos sesiones garantiza pagar menos por cada una de ellas."
            ],
            correct_order=1,
            explanation="El costo por sesión más bajo se obtiene con 4 sesiones por semana.",
            reading_text=READING_PILATES,
            context_image="imagen_3"
        )
        create_question(
            level=rq_basico,
            text="¿Cuál de las siguientes afirmaciones sobre el horario del instructor es incorrecta?",
            options=[
                "Hay más horas disponibles de 8 a.m. a 1 p.m., que de 1 p.m. a 7 p.m.",
                "Todos los días hay 5 horas disponibles.",
                "Hay más horas disponibles de jueves a sábado, que de lunes a miércoles.",
                "El sábado de 12 m. a 7 p.m. no hay clases asignadas."
            ],
            correct_order=2,
            explanation="No todos los días hay exactamente 5 horas disponibles según la tabla.",
            reading_text=READING_PILATES,
            context_image="imagen_3"
        )

        self.stdout.write('✅ Preguntas de Razonamiento Cuantitativo (básico) creadas')

        # ── RAZONAMIENTO CUANTITATIVO - INTERMEDIO ────────────────
        READING_RECICLAJE = (
            "En una ciudad se producen en promedio 600 toneladas diarias de residuos domésticos, "
            "de las cuales el 25% corresponde a papel y cartón, materiales fácilmente reciclables. "
            "Por cada tonelada de papel y cartón que se recicla:\n"
            "- Se evita la tala de 17 árboles adultos.\n"
            "- Se ahorran 140 litros de petróleo y 50.000 litros de agua."
        )

        create_question(
            level=rq_intermedio,
            text="Si se realiza una campaña de reciclaje durante 20 días recolectando 2 toneladas "
                 "diarias de papel y cartón, ¿cuántos litros de agua se podrían ahorrar?",
            options=[
                "680 litros de agua.",
                "5.600 litros de agua.",
                "300.000 litros de agua.",
                "2.000.000 litros de agua."
            ],
            correct_order=4,
            explanation="20 días × 2 toneladas/día × 50.000 litros/tonelada = 2.000.000 litros.",
            reading_text=READING_RECICLAJE
        )
        create_question(
            level=rq_intermedio,
            text="Una persona afirma que como al día se ahorran 140 litros de petróleo por cada "
                 "tonelada reciclada, durante un mes se ahorrarían exactamente 30 veces 140 litros. "
                 "Su afirmación es:",
            options=[
                "Correcta, porque el número 30 indica el número de días que tiene un mes.",
                "Incorrecta, porque debe tener en cuenta las 150 toneladas de papel reciclado por día.",
                "Correcta, porque tiene en cuenta que día tras día hay 140 litros más ahorrado.",
                "Incorrecta, porque debe tener en cuenta las 25 toneladas de papel reciclado por día."
            ],
            correct_order=2,
            explanation="Debe considerar las 150 toneladas diarias (25% de 600) de papel reciclable.",
            reading_text=READING_RECICLAJE
        )

        READING_AVES = (
            "Un científico estudia el comportamiento de cinco aves a lo largo de cuatro sesiones "
            "de 30 minutos cada una. Durante las sesiones, mide el tiempo que le toma a cada ave "
            "realizar cada una de sus actividades y lo registra en una tabla.\n\n"
            "Ave 5: Alimentación 45 min, Desplazamiento 20 min."
        )

        create_question(
            level=rq_intermedio,
            text="Los resultados indican que el ave 5 tarda más alimentándose que desplazándose. "
                 "El tiempo en alimentación excede al de desplazamiento en:",
            options=[
                "20 minutos.",
                "25 minutos.",
                "33 minutos.",
                "45 minutos."
            ],
            correct_order=2,
            explanation="Alimentación: 45 min, Desplazamiento: 20 min. Diferencia: 25 minutos.",
            reading_text=READING_AVES,
            context_image="imagen_aves"
        )
        create_question(
            level=rq_intermedio,
            text="Durante la inversión en seguridad vial 1996-2002, los años con mayor inversión fueron:",
            options=[
                "1997, 1998, 1999 y 2000.",
                "2000, 2001 y 2002.",
                "1999, 2000 y 2001.",
                "1996, 1997, 1998 y 1999."
            ],
            correct_order=2,
            explanation="Los años 2000, 2001 y 2002 muestran las mayores inversiones.",
            reading_text="La gráfica muestra la inversión que hizo un país en temas de seguridad "
                        "vial durante 7 años.",
            context_image="grafica_inversion"
        )

        self.stdout.write('✅ Preguntas de Razonamiento Cuantitativo (intermedio) creadas')

        # ── RAZONAMIENTO CUANTITATIVO - AVANZADO ─────────────────
        READING_JABONES = (
            "Una microempresa de productos de aseo elabora jabón de tocador en dos presentaciones "
            "(barra y líquido) y ofrece tres contenidos en cada una. Cada presentación y contenido "
            "está disponible en tres aromas: natural, coco y vainilla."
        )

        create_question(
            level=rq_avanzado,
            text="La etiqueta del jabón debe especificar: presentación, contenido y aroma. "
                 "¿Cuántas etiquetas diferentes debe utilizar la fábrica?",
            options=[
                "2",
                "6",
                "12",
                "18"
            ],
            correct_order=4,
            explanation="2 presentaciones × 3 contenidos × 3 aromas = 18 combinaciones.",
            reading_text=READING_JABONES,
            context_image="imagen_jabones"
        )
        create_question(
            level=rq_avanzado,
            text="Si se conservara la relación entre el contenido y el precio por unidad, "
                 "¿cuál debería ser el precio del jabón líquido con contenido de 1.800 ml? "
                 "(El de 300ml cuesta $5.100)",
            options=[
                "$15.300",
                "$18.000",
                "$30.600",
                "$31.660"
            ],
            correct_order=3,
            explanation="Precio por mL: 5.100/300 = 17. 1.800 × 17 = $30.600.",
            reading_text=READING_JABONES,
            context_image="imagen_jabones"
        )
        create_question(
            level=rq_avanzado,
            text="Una pista marcada en un extremo con el número 24, en el extremo opuesto "
                 "está marcada con el número:",
            options=[
                "06",
                "18",
                "36",
                "42"
            ],
            correct_order=1,
            explanation="El extremo opuesto: (24 × 10) - 180 = 240 - 180 = 60 → 06.",
            reading_text="Las pistas de aterrizaje se marcan según su alineación con el norte "
                        "magnético. Cada pista recibe dos números según la dirección de la aeronave.",
            context_image="imagen_brujula"
        )

        self.stdout.write('✅ Preguntas de Razonamiento Cuantitativo (avanzado) creadas')

        # ── INGLÉS - FEELINGS ─────────────────────────────────────
        feelings_options = [
            "afraid", "angry", "cold", "happy",
            "hungry", "sad", "thirsty", "tired"
        ]

        create_question(
            level=ing_feelings,
            text="People often cry when they feel like this.",
            options=feelings_options,
            correct_order=6,
            explanation="People cry when they feel sad."
        )
        create_question(
            level=ing_feelings,
            text="If we feel like this, we want to eat something.",
            options=feelings_options,
            correct_order=5,
            explanation="When we feel hungry, we want to eat."
        )
        create_question(
            level=ing_feelings,
            text="When we hate something, we sometimes feel like this.",
            options=feelings_options,
            correct_order=2,
            explanation="Hate often makes people feel angry."
        )
        create_question(
            level=ing_feelings,
            text="Some people usually feel like this when it's hot, and need to drink something.",
            options=feelings_options,
            correct_order=7,
            explanation="When it's hot, people feel thirsty and need to drink."
        )
        create_question(
            level=ing_feelings,
            text="A person feels like this when they need to sleep after a long day.",
            options=feelings_options,
            correct_order=8,
            explanation="After a long day, people feel tired and need to sleep."
        )

        self.stdout.write('✅ Preguntas de Inglés (Feelings) creadas')

        # ── INGLÉS - CONVERSATIONS ────────────────────────────────
        create_question(
            level=ing_conversations,
            text="Do you prefer cats or dogs?",
            options=["Both are nice.", "It's not OK.", "All right."],
            correct_order=1,
            explanation="'Both are nice' is the appropriate response to a preference question."
        )
        create_question(
            level=ing_conversations,
            text="I forgot to turn the lights off.",
            options=["How about this?", "Are you sure?", "Do it this way."],
            correct_order=2,
            explanation="'Are you sure?' is a natural response to forgetfulness."
        )
        create_question(
            level=ing_conversations,
            text="I am afraid my sister is sick.",
            options=["Oh, I'm sorry.", "Too late.", "Can I go now?"],
            correct_order=1,
            explanation="'Oh, I'm sorry' shows empathy for someone's concern about illness."
        )
        create_question(
            level=ing_conversations,
            text="Let's go to the park next weekend.",
            options=["As soon as possible.", "Hope it is.", "Great idea."],
            correct_order=3,
            explanation="'Great idea' shows agreement with a suggestion."
        )
        create_question(
            level=ing_conversations,
            text="Can I talk to you for a minute?",
            options=["Be careful.", "Of course.", "Just one."],
            correct_order=2,
            explanation="'Of course' is a polite way to grant permission."
        )

        self.stdout.write('✅ Preguntas de Inglés (Conversations) creadas')

        # ── INGLÉS - COMPLETE THE TEXT ────────────────────────────
        READING_GREEKS = (
            "Sadly, many people today ___ know the differences between Greeks and Romans. "
            "In fact, the two are very different ___ one another. ___ Greeks and Romans were "
            "great architects. Greeks used to ___ more about shape than function. They ___ "
            "the most important thing was making beautiful buildings. ___, Romans were perfect "
            "engineers. For ___ street planning and use had the greatest importance. "
            "Greeks admired poets and philosophers, ___ Romans admired their soldiers."
        )

        create_question(
            level=ing_text,
            text="Complete: 'Sadly, many people today ___ know the differences between "
                 "Greeks and Romans.'",
            options=["doesn't", "don't", "didn't"],
            correct_order=2,
            explanation="'don't' is the correct plural form for 'many people'.",
            reading_text=READING_GREEKS,
            context_image="geek_and_roman_culture"
        )
        create_question(
            level=ing_text,
            text="Complete: 'In fact, the two are very different ___ one another.'",
            options=["among", "against", "from"],
            correct_order=3,
            explanation="'different from' is the correct prepositional phrase.",
            reading_text=READING_GREEKS,
            context_image="geek_and_roman_culture"
        )
        create_question(
            level=ing_text,
            text="Complete: '___ Greeks and Romans were great architects.'",
            options=["Either", "Both", "Each"],
            correct_order=2,
            explanation="'Both' is used to refer to two groups positively.",
            reading_text=READING_GREEKS,
            context_image="geek_and_roman_culture"
        )
        create_question(
            level=ing_text,
            text="Complete: 'Greeks admired poets and philosophers, ___ Romans admired "
                 "their soldiers.'",
            options=["but", "or", "so"],
            correct_order=1,
            explanation="'but' shows contrast between what Greeks and Romans admired.",
            reading_text=READING_GREEKS,
            context_image="geek_and_roman_culture"
        )
        create_question(
            level=ing_text,
            text="Complete: '___, Romans were perfect engineers.'",
            options=["Almost", "However", "Indeed"],
            correct_order=2,
            explanation="'However' shows contrast with the previous statement about Greeks.",
            reading_text=READING_GREEKS,
            context_image="geek_and_roman_culture"
        )

        self.stdout.write('✅ Preguntas de Inglés (Complete the text) creadas')

        # ── INGLÉS - READING COMPREHENSION ───────────────────────
        READING_ONEIDA = (
            "John Humphrey Noyes travelled to New York State to change his way of life and "
            "create a more equal society. The Oneida building now functions as a hotel with "
            "guest rooms. The library is described as 'unchanged from the original construction'. "
            "They studied Latin and Greek at Oneida. The library, grounds, and several public "
            "rooms are open to guests. The $100 fee includes a private tour of the building."
        )

        create_question(
            level=ing_reading,
            text="John Humphrey Noyes travelled to New York State",
            options=[
                "to visit his family.",
                "to change his way of life.",
                "to know more about his country."
            ],
            correct_order=2,
            explanation="He wanted to live according to his beliefs and create a more equal society.",
            reading_text=READING_ONEIDA,
            context_image="social_experiment_text"
        )
        create_question(
            level=ing_reading,
            text="Nowadays Oneida is",
            options=["a hotel.", "a display.", "a school."],
            correct_order=1,
            explanation="The building now functions as a hotel with guest rooms.",
            reading_text=READING_ONEIDA,
            context_image="social_experiment_text"
        )
        create_question(
            level=ing_reading,
            text="The old library",
            options=[
                "has changed a little.",
                "has remained the same.",
                "has been damaged."
            ],
            correct_order=2,
            explanation="The library is described as 'unchanged from the original construction'.",
            reading_text=READING_ONEIDA,
            context_image="social_experiment_text"
        )
        create_question(
            level=ing_reading,
            text="People at Oneida studied",
            options=["languages.", "politics.", "anatomy."],
            correct_order=1,
            explanation="They studied Latin and Greek, which are languages.",
            reading_text=READING_ONEIDA,
            context_image="social_experiment_text"
        )
        create_question(
            level=ing_reading,
            text="All visitors to the Oneida historical site",
            options=[
                "have access to most parts of the house.",
                "have to go to the 19th century library.",
                "are not allowed to see certain places."
            ],
            correct_order=1,
            explanation="The library, grounds, and several public rooms are open to guests.",
            reading_text=READING_ONEIDA,
            context_image="social_experiment_text"
        )

        self.stdout.write('✅ Preguntas de Inglés (Reading Comprehension) creadas')

        # ── COMPETENCIAS CIUDADANAS - BÁSICO ─────────────────────
        create_question(
            level=cc_basico,
            text="Teniendo en cuenta lo planteado en la Constitución Política de Colombia, "
                 "la respuesta casi nula de la ciudadanía ante un llamado de emergencia refleja:",
            options=[
                "La incapacidad del Gobierno nacional para atender la emergencia.",
                "La deficiencia en la infraestructura nacional para la prevención de desastres.",
                "La inobservancia del principio de solidaridad por parte de los ciudadanos.",
                "La falta de confianza en las instituciones públicas."
            ],
            correct_order=3,
            explanation="La Constitución establece el principio de solidaridad como uno de "
                        "los fundamentos del Estado social de derecho.",
            reading_text=(
                "Después de una fuerte temporada de lluvias, el Gobierno nacional despliega "
                "ayudas para atender a la población afectada. Se hace un llamado a la ciudadanía "
                "para que aporte dinero y materiales. Tras este llamado, la respuesta es casi nula."
            )
        )
        create_question(
            level=cc_basico,
            text="¿Cuál de las siguientes soluciones vulnera el derecho a la educación?",
            options=[
                "Organizar transporte para que los estudiantes vayan a escuelas no afectadas.",
                "Ajustar el calendario para incluir los sábados como día escolar.",
                "Dar clases a través de tutores a domicilio para reducir días presenciales.",
                "Trasladar a los niños a escuelas no inundadas dos veces por semana y "
                "reducir el número de clases presenciales."
            ],
            correct_order=4,
            explanation="Reducir significativamente las clases presenciales vulnera el derecho "
                        "a la educación al limitar el acceso regular.",
            reading_text=(
                "Durante las épocas de lluvias, en muchas zonas rurales de Colombia se inundan "
                "escuelas y se interrumpen los caminos para llegar a estas."
            )
        )
        create_question(
            level=cc_basico,
            text="¿Cuál es el organismo encargado de elegir al Contralor General de la República?",
            options=[
                "La Presidencia de la República.",
                "La Corte Constitucional.",
                "El Congreso de la República.",
                "El Consejo de Estado."
            ],
            correct_order=3,
            explanation="Según la Constitución, el Contralor General es elegido por el Congreso."
        )
        create_question(
            level=cc_basico,
            text="¿Por qué el proyecto que condena el satanismo por ser contrario a las creencias "
                 "de la mayoría no podría aprobarse?",
            options=[
                "Porque contradice la Constitución, que protege todas las creencias religiosas.",
                "Porque contradice los derechos de los legisladores de religiones minoritarias.",
                "Porque contradice normas internacionales sobre las iglesias y los Estados.",
                "Porque contradice las leyes que establecen que la religión es un asunto privado."
            ],
            correct_order=1,
            explanation="La Constitución garantiza la libertad de cultos e igualdad de religiones.",
            reading_text=(
                "Recientemente se propuso un proyecto de ley que condena el satanismo, porque "
                "es contrario a las creencias religiosas de la mayoría de la población colombiana."
            )
        )
        create_question(
            level=cc_basico,
            text="Una colombiana devota del islam lleva pañoleta en la cabeza. En una entrevista "
                 "para un cargo público, le advierten que no puede tomar el trabajo si no acepta "
                 "llevar la cabeza descubierta. ¿Tiene razón el funcionario?",
            options=[
                "Sí, porque Colombia es un país católico.",
                "Sí, porque el Estado colombiano es laico.",
                "No, porque le está vulnerando el derecho a la privacidad.",
                "No, porque le está vulnerando el derecho a la igualdad."
            ],
            correct_order=4,
            explanation="La Constitución garantiza la igualdad y libertad de cultos; "
                        "no se puede discriminar por motivos religiosos."
        )
        create_question(
            level=cc_basico,
            text="De acuerdo con la Constitución, ¿podrían los ciudadanos acudir a un mecanismo "
                 "de participación directa para pronunciarse sobre la pena de muerte?",
            options=[
                "No, los asuntos penales son competencia exclusiva de la Rama Judicial.",
                "No, la decisión debe ser tomada por el presidente vía decreto.",
                "Sí, a través de un referendo constitucional.",
                "No, solo el Congreso puede modificar la Constitución."
            ],
            correct_order=3,
            explanation="El referendo constitucional es un mecanismo de participación ciudadana.",
            reading_text=(
                "Suponga que en el país se discute la conveniencia de reformar la Constitución "
                "para permitir la pena de muerte."
            )
        )

        self.stdout.write('✅ Preguntas de Competencias Ciudadanas (básico) creadas')

        # ── COMPETENCIAS CIUDADANAS - INTERMEDIO ──────────────────
        create_question(
            level=cc_intermedio,
            text="Las divergencias entre científicos y activistas sobre el uso de cerdos en "
                 "experimentos radican en que:",
            options=[
                "Los activistas quieren oponerse al desarrollo económico.",
                "Los activistas quieren cuestionar la efectividad de la ciencia.",
                "Los científicos quieren utilizar animales como instrumentos de investigación.",
                "Los científicos quieren priorizar la vida humana, mientras que los activistas "
                "quieren proteger lo que consideran un derecho de los animales a su propia vida."
            ],
            correct_order=4,
            explanation="La divergencia central está en la priorización: vida humana vs. "
                        "derechos de los animales.",
            reading_text=(
                "Un grupo de activistas busca evitar que un centro de investigación siga "
                "utilizando cerdos para experimentos. Los investigadores defienden su uso, "
                "pues estos animales proveen la mejor plataforma para desarrollar medicinas "
                "sin poner en riesgo vidas humanas."
            )
        )
        create_question(
            level=cc_intermedio,
            text="Al evaluar el cierre de sectores residenciales para seguridad privada, "
                 "¿qué intereses podrían entrar en conflicto?",
            options=[
                "Los de las empresas de seguridad privada y los de los residentes.",
                "Los de los residentes que buscan seguridad, y los de los demás habitantes "
                "que dejarían de tener acceso a vías y espacios públicos.",
                "Los de los residentes y los intereses del gobierno local.",
                "Los de las empresas de seguridad privada que serían contratadas."
            ],
            correct_order=2,
            explanation="El conflicto principal: seguridad privada de algunos vs. "
                        "acceso público de todos.",
            reading_text=(
                "Ante crecientes robos, el alcalde considera autorizar el cierre de grandes "
                "sectores residenciales para que sean vigilados por seguridad privada y solo "
                "permitan entrada a residentes autorizados."
            )
        )
        create_question(
            level=cc_intermedio,
            text="En la situación de las caricaturas de Mahoma publicadas en Dinamarca, "
                 "¿qué aspectos están en conflicto?",
            options=[
                "Las democracias europeas y las teocracias de Oriente.",
                "Las religiones occidentales y las religiones orientales.",
                "La libertad de expresión de los caricaturistas y las creencias religiosas "
                "de un grupo de personas.",
                "Los valores culturales de Europa y las tradiciones ancestrales de Asia."
            ],
            correct_order=3,
            explanation="El conflicto central: derecho a la libertad de expresión vs. "
                        "respeto a las creencias religiosas.",
            reading_text=(
                "En 2005 un periódico danés publicó doce caricaturas sobre Mahoma, "
                "despertando la rabia de muchos musulmanes que protestaron por este hecho."
            )
        )
        create_question(
            level=cc_intermedio,
            text="¿Cuál de los siguientes argumentos respalda la decisión de la Corte de "
                 "extender beneficios del régimen de salud a parejas homosexuales?",
            options=[
                "Se requiere garantizar la igualdad de derechos para todos los ciudadanos.",
                "Es necesaria la protección de los derechos de los ciudadanos pensionados.",
                "Se requiere proteger los derechos del matrimonio entre hombres y mujeres.",
                "La Constitución no reconoce los derechos patrimoniales de parejas del mismo sexo."
            ],
            correct_order=1,
            explanation="La Corte Constitucional fundamentó su decisión en el principio de "
                        "igualdad consagrado en la Constitución.",
            reading_text=(
                "Entre 2007 y 2008, la Corte Constitucional extendió a parejas homosexuales "
                "los beneficios del régimen contributivo de salud y del derecho a la pensión."
            )
        )

        self.stdout.write('✅ Preguntas de Competencias Ciudadanas (intermedio) creadas')

        # ── COMPETENCIAS CIUDADANAS - AVANZADO ───────────────────
        create_question(
            level=cc_avanzado,
            text="¿Cuál es un argumento válido para contradecir la postura de que los "
                 "policías de tránsito causan las congestiones vehiculares?",
            options=[
                "Los policías no deben ser cuestionados, ya que representan a una institución.",
                "El hecho de que los policías estén donde hay congestiones no quiere decir "
                "que ellos las originen.",
                "Los policías hacen su labor, pero no son suficientes para evitar congestiones.",
                "El hecho de que haya congestiones no significa que los policías no estén capacitados."
            ],
            correct_order=2,
            explanation="Este argumento identifica correctamente la falacia de "
                        "correlación-causalidad.",
            reading_text=(
                "Algunas personas culpan a los policías de tránsito de las congestiones, "
                "porque observan que cuando hay una gran congestión es frecuente que haya "
                "un policía guiando el tránsito."
            )
        )
        create_question(
            level=cc_avanzado,
            text="¿Cuál de los siguientes es un argumento a favor de la legalización de drogas?",
            options=[
                "Una gran parte de la violencia está asociada al tráfico de drogas, "
                "por tanto su comercialización debe tener estrictos controles.",
                "En los países productores no existe responsabilidad en el tráfico de drogas.",
                "Una gran parte de quienes consumen drogas son personas enfermas que necesitan apoyo.",
                "En los países productores, la prohibición ha generado problemas sociales más "
                "graves que los efectos que se querían evitar."
            ],
            correct_order=4,
            explanation="Este argumento sostiene que la prohibición genera más problemas "
                        "sociales que los que pretende evitar.",
            reading_text=(
                "El problema del tráfico de drogas ha generado debates entre gobernantes y "
                "académicos. Algunos proponen que, para defender el bien común, se deben "
                "legalizar las drogas."
            )
        )
        create_question(
            level=cc_avanzado,
            text="Al negarse a recibir una transfusión por sus creencias religiosas, "
                 "¿qué dimensión está privilegiando la paciente?",
            options=[
                "Sus creencias religiosas y el estilo de vida que ellas exigen.",
                "Las consecuencias en su salud y estado físico en un futuro.",
                "Las recomendaciones médicas y evidencia científica.",
                "La decisión familiar como base para el consentimiento médico."
            ],
            correct_order=1,
            explanation="La paciente privilegia sus creencias religiosas sobre las "
                        "recomendaciones médicas.",
            reading_text=(
                "Una paciente debe someterse a cirugía. El médico le advierte que podría "
                "haber hemorragia. La paciente inicialmente firma el consentimiento para "
                "transfusiones pero luego cambia de opinión por razones religiosas."
            )
        )
        create_question(
            level=cc_avanzado,
            text="En relación con el análisis del FMI sobre América Latina, el argumento de "
                 "la analista económica es válido al:",
            options=[
                "Respaldar el concepto del FMI, mostrando que se subutiliza el potencial femenino.",
                "Refutar el análisis del FMI, demostrando que la desigualdad de género es el "
                "principal obstáculo para el desarrollo, no la falta de tecnología.",
                "Rechazar el diagnóstico del FMI, demostrando que la innovación tecnológica "
                "no tiene efecto en el desarrollo.",
                "Apoyar la explicación del FMI, pues ambos muestran que la mujer ha aumentado "
                "su participación laboral."
            ],
            correct_order=2,
            explanation="La analista refuta el FMI al mostrar que la desigualdad de género "
                        "es un obstáculo más fundamental que la falta de tecnología.",
            reading_text=(
                "El FMI enfatizó que en América Latina se evidencian altas tasas de "
                "participación laboral y resaltó la innovación tecnológica como principal "
                "reto para el desarrollo. Una analista sostuvo que el verdadero problema "
                "es que el 50% de las mujeres se dedica a la economía del cuidado sin "
                "reconocimiento económico ni social."
            )
        )

        self.stdout.write('✅ Preguntas de Competencias Ciudadanas (avanzado) creadas')

        # ── RESUMEN FINAL ─────────────────────────────────────────
        total_questions = Question.objects.count()
        total_options = QuestionOption.objects.count()
        total_levels = Level.objects.count()
        total_competences = Competence.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Población completada exitosamente:\n'
            f'   📚 {total_competences} competencias\n'
            f'   📊 {total_levels} niveles\n'
            f'   ❓ {total_questions} preguntas\n'
            f'   🔤 {total_options} opciones de respuesta'
        ))