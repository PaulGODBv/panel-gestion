# Reta2 — Panel de gestión y API

Backend y panel de administración de **Reta2**, una aplicación educativa de
práctica por competencias. Este repositorio expone la API REST que consume la
app Android y el panel web donde los docentes gestionan el banco de preguntas y
siguen el progreso de los estudiantes.

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
│  · sincroniza reportes  │  Key    │  · ranking y dashboard       │
└─────────────────────────┘         └──────────────────────────────┘
```

La app funciona sin conexión: guarda preguntas y progreso en Room y sincroniza
los reportes cuando hay red. El panel es la fuente de verdad del contenido
académico.

## Aplicaciones Django

| App         | Responsabilidad                                                        |
|-------------|------------------------------------------------------------------------|
| `academics` | Contenido académico: competencias, niveles, preguntas, opciones e imágenes de contexto |
| `core`      | Reportes de estudiantes, progreso por nivel, ranking y dashboard       |

### Modelo de contenido (`academics`)

```
Competence  ──┬──► Level  ──┬──► Question  ──► QuestionOption
              │             │
           (orden)       (orden,              ContextAsset
                      formato_practica)      (imagen + alt_text)
```

`Question` lleva historial de cambios con `django-simple-history`
(`HistoricalQuestion`), así que toda edición del banco de preguntas queda
auditada: quién la hizo y qué cambió.

### Reportes (`core`)

```
StudentReport  ──► LevelProgressReport
```

`StudentReport` acumula las métricas que envía la app (preguntas respondidas,
tiempo de práctica, racha actual y mejor racha), y `LevelProgressReport`
desglosa el puntaje y el tiempo nivel por nivel.

## API REST

Todos los endpoints viven bajo `/api/`.

| Método | Endpoint                           | Autenticación | Descripción                              |
|--------|------------------------------------|---------------|------------------------------------------|
| GET    | `/competences/`                    | API Key       | Competencias con sus niveles             |
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

| Variable                | Obligatoria        | Descripción                                        |
|-------------------------|--------------------|----------------------------------------------------|
| `RETA2_API_KEY`         | siempre            | Clave compartida con la app Android (`X-API-Key`)  |
| `DJANGO_SECRET_KEY`     | si `DEBUG=False`   | Clave de firma de Django                           |
| `DJANGO_DEBUG`          | no (default `True`)| `False` para producción                            |
| `DJANGO_ALLOWED_HOSTS`  | si `DEBUG=False`   | Dominios separados por coma                        |

Generar las claves:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

La misma `RETA2_API_KEY` debe quedar en `ApiConfig.API_KEY` de la app Android,
o la API rechaza todas sus peticiones.

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

| Ruta      | Contenido                                                  |
|-----------|------------------------------------------------------------|
| `/admin/` | Admin de Django con tema Unfold: edición del banco de preguntas |
| `/panel/` | Vistas propias de reportes y dashboard (`core/urls_admin.py`) |
| `/api/`   | API REST que consume la app Android                        |

## Notas de seguridad

- `SECRET_KEY`, `RETA2_API_KEY` y `ALLOWED_HOSTS` se leen del entorno. Con
  `DEBUG=False`, si falta alguna el arranque se detiene con un mensaje claro en
  lugar de quedar funcionando con un valor por defecto público.
- La base de datos de desarrollo y sus respaldos (`db-antes-*.sqlite3`) están
  ignorados: contienen datos de trabajo y no pertenecen al repositorio.
- Una clave anterior quedó expuesta en el historial de git y fue rotada. Una
  credencial comprometida que sigue funcionando es peor que ninguna.

## Documentación interna

| Archivo                                | Contenido                                     |
|----------------------------------------|-----------------------------------------------|
| `docs/conciliacion-banco-preguntas.md` | Conciliación del banco de preguntas           |
| `docs/tablero-trello.md`               | Seguimiento de tareas                         |

## Licencia

Proyecto académico — Universidad de Santander (UDES).
