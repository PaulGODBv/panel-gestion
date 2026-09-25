# Tablero Kanban — «Trabajo de grado»

Contenido listo para volcar en Trello (https://trello.com/b/E0s3m3iw/trabajo-de-grado).
Cuatro columnas, las que fija la Fase 4 del anteproyecto.

> Pendiente de aplicar: la escritura en Trello quedó bloqueada por permisos
> («External System Writes»). En cuanto se autorice, se crea en una pasada.

## Backlog

| Tarjeta | Descripción |
| --- | --- |
| Despliegue en producción | Azure Container Apps. Hoy solo corre en red local. |
| Migrar a PostgreSQL | SQLite es suficiente en desarrollo, no para la prueba piloto. |
| Endurecer configuración | `DEBUG=False`, `SECRET_KEY` y `RETA2_API_KEY` por variable de entorno, quitar `'*'` de `ALLOWED_HOSTS`, servir por HTTPS y retirar el permiso de tráfico en claro del manifiesto Android. |
| Hash a PBKDF2 o Argon2 | SHA-256 con salt frena tablas precalculadas pero no fuerza bruta dirigida. Acotado a `PasswordHasher.computeHash()`. |
| Migraciones Room no destructivas | Hoy `fallbackToDestructiveMigration()` borra el progreso al subir de versión. |
| APK final y prueba piloto | Objetivo 3 del anteproyecto: usabilidad y pertinencia de las métricas. |
| Modo competitivo multijugador | Trabajo futuro, requiere WebSockets. |

## Por hacer

| Tarjeta | Descripción |
| --- | --- |
| TODO-1 · El panel como fuente de verdad del banco | Decidido el 24/09/2026. El administrador sube, la app descarga y cachea en Room. Cinco pasos en `ENTORNO_REGLAS_NEGOCIO_Y_DISENO.md`. |
| TODO-2 · Carga de preguntas amigable | Las cartillas llegan en PDF con imágenes. Los tres caminos actuales (formulario, CSV, script) no sirven para quien no es desarrollador. |
| TODO-3 · Imagen de contexto como archivo | `context_image` es hoy un `CharField`. Pasa a `ImageField` + `MEDIA_*` + URL en la API + descarga en la app. |
| TODO-4 · Esqueleto de carga | Se muestra siempre y no distingue primera composición de búsqueda de conexión. Los grises están fijos en código (`PremiumUxComponents.kt`), por eso contrasta tanto en oscuro. |
| TODO-5 · Botón de cambio de tema | 38×38 px, superpuesto al contenido, esquina superior derecha, visible en todo momento. |
| TODO-6 · Estadísticos y explorador | Moda de competencias, media por programa y competencia, y un gráfico filtrable por programa × competencia × nivel × fechas. |
| TODO-7 · Animaciones de Material Design | Transiciones entre pantallas, respuesta al pulsar, entrada de listas, feedback de acierto y error. |
| TODO-8 · Paleta del modo oscuro | Tres opciones propuestas el 24/09/2026. Pendiente de elegir. |
| TODO-B · Nivel de Comunicación Escrita | El módulo del Icfes es de pregunta abierta; se sustituye con ítems cerrados sobre sus tres ejes de calificación. |

## En progreso

| Tarjeta | Descripción |
| --- | --- |
| TODO-A · Umbral de aprobación al 70 % | Código hecho: `domain/LevelRules.kt` con el valor único que leen la pantalla de resultados y `ProgressRepositoriesImp`. **Falta compilar y probar en dispositivo** (Gradle no levanta el daemon en el entorno de trabajo). |

## Terminado

| Tarjeta | Descripción |
| --- | --- |
| App móvil: 4 competencias, 13 niveles | Preguntas aleatorias sin repetir, con priorización de las falladas. |
| Modo contrarreloj | Tres fuentes de preguntas y tiempo configurable de 3 a 9 minutos. |
| Gamificación | Niveles progresivos, rachas, insignias y progreso visual. |
| Contraseñas hasheadas | SHA-256 con salt por usuario, verificación de la actual al cambiarla. |
| Validación de correo institucional | `@mail.udes.edu.co` en el registro de la app y en el serializador. |
| Panel Django con Unfold y API REST | Siete endpoints, sidebar propio y paleta azul UDES. |
| Dashboard | KPIs, heatmap anual, progreso por competencia y comparativa por programa. |
| Seguimiento de estudiantes | Búsqueda, filtro por fechas, exportación CSV y clasificación de riesgo. |
| Banco de preguntas en el panel | Importación CSV, vista previa tipo móvil, cobertura por nivel e historial de cambios. |
| Rediseño visual del panel | Sistema Dovetail: tokens sobre Unfold, componentes `.rt-*`, responsive verificado. |
| API cerrada | Cabecera `X-API-Key` en los endpoints de la app; sesión de staff en los del panel. |
| Programa académico en la sincronización | Alimenta la comparativa por cohortes, que antes salía vacía. |
| Animaciones del panel | Cifras que cuentan, cambio de tema con barrido circular, barra lateral escalonada y rueda aislada. |
| Sincronización manual en Progreso | Automática en el splash, manual desde Progreso. El botón de Inicio no sincronizaba nada. |
| Iconografía Material sin emojis | Toda la interfaz de la app. |
