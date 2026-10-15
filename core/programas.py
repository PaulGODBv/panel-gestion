"""Los programas académicos de la UDES Bucaramanga, y cómo comparar nombres.

De dónde sale la lista: bucaramanga.udes.edu.co/estudia, leída el 15/10/2026.
Solo pregrados, tecnologías y técnicos laborales — ni posgrados, ni diplomados,
ni cursos: la app es para Saber Pro, que se presenta al terminar pregrado.

**Este fichero es el gemelo de `ProgramasUdes.kt` en la app.** Los dos tienen
que decir lo mismo, y por eso los dos citan la misma fuente y la misma fecha.
Se duplica a propósito en vez de que el panel se la sirva a la app: el registro
ocurre antes de que haya sesión y puede ocurrir sin datos, así que la app tiene
que llevarla dentro. Si alguna vez cambia, hay que tocar los dos.

POR QUÉ EXISTE. El programa se escribía a mano en la app, y en el panel
convivían «Ingeniería de software» e «Ingeniería de Software» como si fueran
dos carreras. Desde la versión que trae el selector, la app manda la grafía de
este catálogo y el problema no vuelve a aparecer. Lo que este módulo resuelve
es lo que ya está escrito y no se puede reescribir: los reportes viejos.
"""

import unicodedata

# Los 33 pregrados.
PREGRADOS = [
    "Administración de Empresas (Virtual)",
    "Administración de Negocios Internacionales",
    "Administración Financiera",
    "Antropología",
    "Bacteriología y Laboratorio Clínico",
    "Comunicación Social y Periodismo",
    "Contaduría Pública",
    "Contaduría Pública (Virtual)",
    "Derecho",
    "Economía (Virtual)",
    "Enfermería",
    "Fisioterapia",
    "Fonoaudiología",
    "Geología",
    "Ingeniería Agroindustrial",
    "Ingeniería Ambiental",
    "Ingeniería Civil",
    "Ingeniería de Software",
    "Ingeniería de Software (Virtual)",
    "Ingeniería en Ciencias de la Computación e Inteligencia Artificial",
    "Ingeniería en Energías",
    "Ingeniería Industrial",
    "Ingeniería Industrial (Virtual)",
    "Ingeniería Petroquímica",
    "Instrumentación Quirúrgica",
    "Licenciatura en Educación Infantil",
    "Medicina",
    "Medicina Veterinaria",
    "Mercadeo y Publicidad",
    "Microbiología Industrial",
    "Psicología",
    "Relaciones y Negocios Internacionales (Virtual)",
    "Terapia Ocupacional",
]

# Las 3 tecnologías.
TECNOLOGIAS = [
    "Tecnología en Comunicación Gráfica",
    "Tecnología en Gestión Logística del Comercio Exterior",
    "Tecnología en Supervisión de Obras Civiles",
]

# Los 13 técnicos laborales.
TECNICOS = [
    "Técnico Intermedio en Producción de Biomateriales en el Sector Avícola, Pecuario y Otros",
    "Técnico Laboral en Auxiliar Administrativo",
    "Técnico Laboral en Auxiliar de Avalúos",
    "Técnico Laboral en Auxiliar de Educación para la Primera Infancia",
    "Técnico Laboral en Auxiliar de Servicios de Recreación y Deportes",
    "Técnico Laboral en Auxiliar de Ventas por Canales Digitales",
    "Técnico Laboral en Información Turística",
    "Técnico Laboral en Información y Servicio al Cliente",
    "Técnico Laboral en Instalación y Mantenimiento de Sistemas Solares Fotovoltaicos",
    "Técnico Laboral en Manejo de Herramientas para Codificación de Software",
    "Técnico Laboral en Servicios de Cartera y Cobranzas",
    "Técnico Laboral por Competencias en Auxiliar de Clínica Veterinaria",
    "Técnico Laboral por Competencias en Auxiliar en Galponería Avícola",
]

NIVEL_PREGRADO = "pregrado"
NIVEL_TECNOLOGIA = "tecnologia"
NIVEL_TECNICO = "tecnico"

#: Los 49, cada uno con su nivel. El nivel sirve para agrupar en el panel sin
#: tener que adivinarlo del nombre.
CATALOGO = (
    [(nombre, NIVEL_PREGRADO) for nombre in PREGRADOS]
    + [(nombre, NIVEL_TECNOLOGIA) for nombre in TECNOLOGIAS]
    + [(nombre, NIVEL_TECNICO) for nombre in TECNICOS]
)


def normalizar(texto):
    """La forma en que se comparan dos nombres de programa.

    Minúsculas, sin tildes, sin espacios de sobra. Es lo que hace que
    «Ingeniería de software» y «INGENIERIA DE SOFTWARE» sean el mismo
    programa, que es el caso que de verdad estaba en los datos.

    Lo que **no** hace es adivinar. «Admon Negocios Internacionales» y
    «Administración de Negocios Internacionales» no se parecen lo suficiente
    para que ningún algoritmo decida por su cuenta que son lo mismo, y
    equivocarse ahí mete un error silencioso en los resultados. Eso lo decide
    una persona, una vez, desde el admin.
    """
    if not texto:
        return ""
    sin_tildes = unicodedata.normalize("NFD", texto.strip().lower())
    sin_tildes = "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.split())
