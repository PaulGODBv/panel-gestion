# Reta2 — Panel de gestión y API

Backend, panel de administración y página pública de **Reta2**, una aplicación
educativa de práctica por competencias para la preparación de las pruebas
Saber Pro. Este repositorio expone la API REST que consume la app Android, el
panel web donde se gestiona el banco de preguntas y se sigue el progreso de los
estudiantes, y la página de presentación desde la que se descarga la app.

**Aplicación Android (cliente):** [PaulGODBv/app](https://github.com/PaulGODBv/app)

**Stack:** Django 6 · Django REST Framework · SQLite · Unfold (tema del admin)

---

## Arquitectura

Reta2 son dos piezas que se comunican por HTTP:

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│   App Android (Kotlin)  │         │  Panel de gestión (Django)   │
│   Jetpack Compose       │         │  ESTE REPOSITORIO            │
│                         │         │                              │
│  · practica offline     │  HTTP   │  · banco de preguntas        │
│  · progreso local       │ ──────► │  · API REST                  │
│    (Room)               │ X-API-  │  · reportes de estudiantes   │
│  · sincroniza reportes  │  Key    │  · métricas y explorador     │
└─────────────────────────┘         └──────────────────────────────┘
```

La app funciona sin conexión: guarda preguntas y progreso en Room y sincroniza
los reportes cuando hay red. **El panel es la fuente de verdad del contenido
académico**, y desde octubre de 2026 también del catálogo: la app pregunta qué
competencias y niveles existen en vez de llevarlos escritos, así que dar de
alta un nivel aquí ya no exige publicar una versión de la app.

## Aplicaciones Django

| App         | Responsabilidad                                                        |
|-------------|------------------------------------------------------------------------|
| `academics` | Contenido académico: competencias, niveles, preguntas, opciones e imágenes de contexto |
| `core`      | Reportes de estudiantes, progreso por nivel, métricas, explorador, página pública y roles |

### Modelo de contenido (`academics`)

```
Competence  ──┬──► Level  ──┬──► Question  ──► QuestionOption
              │             │
           (orden)       (orden,              ContextAsset
                      formato_practica)      (imagen + alt_text)
```

`Question` lleva historial de cambios con `django-simple-history`
(`HistoricalQuestion`), así que toda edición del banco queda auditada: quién la
hizo y qué cambió.

`ContextAsset.es_figura` distingue una figura de línea —una tabla, una
gráfica— de una fotografía o una viñeta. A las primeras se les quita el papel
blanco para que se integren con el tema oscuro de la app; a las segundas no,
porque ahí el blanco significa algo y el resultado sería un negativo.

### Reportes (`core`)

```
StudentReport  ──► LevelProgressReport
```

**Un reporte es una foto, no un suceso.** Cada sincronización manda el estado
completo del estudiante, así que la misma práctica reaparece en todas las fotos
posteriores. Por eso las métricas se calculan sobre **el último reporte de cada
estudiante**, definido en un solo sitio (`core/metricas.py`) para que no pueda
divergir entre dos pantallas. Agregando sobre todos los reportes, el tablero
llegó a decir 2 015 preguntas donde había 93.

## El panel

| Ruta                            | Contenido                                                      |
|---------------------------------|----------------------------------------------------------------|
| `/`                             | Página de presentación: qué es la app, cómo se instala y descarga |
| `/admin/`                       | Admin con tema Unfold: banco de preguntas y cuentas            |
| `/panel/estudiantes/`           | Lista de estudiantes, ficha individual y exportación a CSV     |
| `/panel/explorador/`            | Métricas cruzadas por programa, competencia, nivel y fechas    |
| `/api/`                         | API REST que consume la app Android                            |

### Carga de preguntas

Quien sube las preguntas no es quien programó el panel, así que hay un camino
que no exige conocer el formato: **`/admin/academics/question/importar/`**,
donde se pega el texto tal como venga de una cartilla. Dos símbolos bastan —
`*` marca la correcta, `-` las demás, `>` la explicación y `Contexto:` el
pasaje. Se revisa antes de escribir, entra todo o no entra nada, y detecta las
que ya están en ese nivel.

### Papeles

| | Administrador | Superadministrador |
|---|---|---|
| Banco de preguntas | crear y editar | todo |
| Métricas y fichas | sí | sí |
| Borrar contenido | **no** | sí |
| Cuentas del panel | **no** | sí |

Se aplica con permisos de Django y el grupo `Administradores`, que se mantiene
solo en cada `migrate`. Borrar una competencia se lleva sus niveles y sus
preguntas en cascada, y eso no se deshace desde ninguna pantalla: de ahí que el
administrador no borre.

## API REST

Todos los endpoints viven bajo `/api/`.

| Método | Endpoint                           | Autenticación | Descripción                              |
|--------|------------------------------------|---------------|------------------------------------------|
| GET    | `/competences/`                    | API Key       | Catálogo: competencias con sus niveles   |
| GET    | `/questions/<level_id>/`           | API Key       | Preguntas de un nivel, con opciones      |
| POST   | `/reports/sync/`                   | API Key       | La app sincroniza el progreso            |
| GET    | `/ranking/`                        | API Key       | Ranking de estudiantes                   |
| GET    | `/reports/students/`               | Sesión staff  | Listado de estudiantes                   |
| GET    | `/reports/students/<username>/`    | Sesión staff  | Detalle de un estudiante                 |
| GET    | `/dashboard-data/`                 | Sesión staff  | Series para los gráficos del panel       |

### Autenticación

El permiso por defecto es `IsAdminUser`: **nadie entra si la vista no declara
lo contrario**. Cada vista elige explícitamente su permiso.

- **App Android** → cabecera `X-API-Key` validada contra `RETA2_API_KEY`
  (`core/permissions.py`, clase `HasValidApiKey`).
- **Panel web** → sesión de usuario con `is_staff`.

Antes el default era `AllowAny` y cualquiera podía escribir reportes. Cerrarlo
desde la configuración y no vista por vista evita que una vista nueva quede
abierta por olvido.

El registro de estudiantes exige correo `@mail.udes.edu.co`.

## Instalación

```bash
git clone https://github.com/PaulGODBv/panel-gestion.git
cd panel-gestion

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / macOS

pip install -r requirements.txt
```

### Variables de entorno

| Variable                    | Obligatoria        | Descripción                                        |
|-----------------------------|--------------------|----------------------------------------------------|
| `RETA2_API_KEY`             | siempre            | Clave compartida con la app Android (`X-API-Key`)  |
| `DJANGO_SECRET_KEY`         | si `DEBUG=False`   | Clave de firma de Django                           |
| `DJANGO_DEBUG`              | no (default `True`)| `False` para producción                            |
| `DJANGO_ALLOWED_HOSTS`      | si `DEBUG=False`   | Dominios separados por coma                        |
| `RETA2_VIDEO_PRESENTACION`  | no                 | Dirección de inserción del vídeo de la página pública |

Generar las claves:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

La misma `RETA2_API_KEY` debe quedar en el `local.properties` de la app Android
—que no se versiona— o la API rechaza todas sus peticiones.

En desarrollo (`DEBUG=True`) `ALLOWED_HOSTS` es `['*']`, para que el teléfono
pueda entrar por la IP de la LAN sin reconfigurar nada en cada red.

### Puesta en marcha

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

El `0.0.0.0` es necesario para que el teléfono alcance el servidor en la red
local.

### Página de presentación

Vive en `/` y se adapta a lo que haya: mientras no estén los archivos no enseña
un botón roto ni un reproductor vacío.

| Archivo                           | Para qué                                   |
|-----------------------------------|--------------------------------------------|
| `media/apk/reta2.apk`             | El APK **firmado** que se ofrece en descarga |
| `media/landing/presentacion.mp4`  | Vídeo, si se sirve desde aquí              |

Las dos carpetas están fuera de git: son productos de compilación, no código.

### Pruebas

```bash
python manage.py test core
```

Cubren las cifras del tablero —con una regresión que reproduce el error de
agregación—, los estados vacíos, la visita guiada y la separación de papeles.

## Notas de seguridad

- `SECRET_KEY`, `RETA2_API_KEY` y `ALLOWED_HOSTS` se leen del entorno. Con
  `DEBUG=False`, si falta alguna el arranque se detiene con un mensaje claro en
  lugar de quedar funcionando con un valor por defecto público.
- La base de datos de desarrollo y sus respaldos (`db-antes-*.sqlite3`) están
  ignorados: contienen datos de trabajo y no pertenecen al repositorio.
- Una clave anterior quedó expuesta en el historial de git y fue rotada. Una
  credencial comprometida que sigue funcionando es peor que ninguna.
- ~~La API viaja en claro.~~ **Resuelto el 14/10/2026.** El panel está
  desplegado y sirve por HTTPS, y la app apunta al dominio: el APK de release ya
  no lleva `usesCleartextTraffic`, que solo existe en las compilaciones de
  desarrollo. Rotar la clave nunca arregló esto, porque el problema no era la
  clave sino el canal.
- La contraseña del PostgreSQL de producción se rotó al publicar la guía de
  despliegue: esa guía nombra al usuario y al servidor, y el cortafuegos deja
  entrar a «servicios de Azure», que es cualquier tenant. Usuario conocido más
  contraseña débil sí era una puerta.

## Documentación interna

| Archivo                                | Contenido                                     |
|----------------------------------------|-----------------------------------------------|
| `docs/conciliacion-banco-preguntas.md` | Conciliación del banco de preguntas           |
| `docs/preguntas-calentamiento.md`      | Versiones cortas para los niveles de práctica |
| `docs/tablero-trello.md`               | Seguimiento de tareas                         |
| `docs/despliegue.md`                   | Despliegue en Azure, CI/CD y lo que costó cada paso |

## Despliegue

El panel está en **Azure Container Apps** con PostgreSQL gestionado, y **empujar
a `main` despliega**: GitHub Actions corre las pruebas, `check --deploy` y
`makemigrations --check`, y solo si pasan construye la imagen etiquetada con el
sha del commit, la sube y espera a que el sitio responda 200 antes de darse por
buena. No hay camino que despliegue sin pasar por las pruebas.

Los dos ficheros están en `.github/workflows/`. Todo lo demás —el montaje de la
identidad federada, y los tropiezos que costaron un intento cada uno— está en
`docs/despliegue.md`.

## Licencia

Proyecto académico — Universidad de Santander (UDES).
