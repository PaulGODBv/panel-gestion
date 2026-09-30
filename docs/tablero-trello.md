# Tablero Kanban — «Trabajo de grado»

Contenido listo para volcar en Trello (https://trello.com/b/E0s3m3iw/trabajo-de-grado).
Cuatro columnas, las que fija la Fase 4 del anteproyecto.

> **Aplicado el 24/09/2026.** El tablero existe con las cuatro columnas y 34
> tarjetas. Este archivo queda como copia de respaldo del contenido: si se
> reorganiza el tablero, la fuente de verdad pasa a ser Trello.

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
| TODO-2 · Carga de preguntas amigable | Las cartillas llegan en PDF con imágenes. Los tres caminos actuales (formulario, CSV, script) no sirven para quien no es desarrollador. |
| TODO-3 · Imagen de contexto como archivo | `context_image` es hoy un `CharField`. Pasa a `ImageField` + `MEDIA_*` + URL en la API + descarga en la app. |
| TODO-6 · Estadísticos y explorador | Moda de competencias, media por programa y competencia, y un gráfico filtrable por programa × competencia × nivel × fechas. |
| TODO-7 · Animaciones de Material Design | Transiciones entre pantallas, entrada de listas, feedback de acierto y error. La respuesta al pulsar ya está hecha en la barra de navegación (25/09/2026). |
| TODO-B · Nivel de Comunicación Escrita | El módulo del Icfes es de pregunta abierta; se sustituye con ítems cerrados sobre sus tres ejes de calificación. |
| Decidir si la sesión crece con el nivel | `calculateQuestionCount()` devuelve 5 para todos los niveles, así que el umbral del 70 % no cambia nada todavía. |

## En progreso

| Tarjeta | Descripción |
| --- | --- |
| TODO-1 · El panel como fuente de verdad del banco | **Paso 0 hecho:** CompetencyData tiene los originales y el panel se sembró desde él (41 creadas, 36 corregidas). De 60 a 101 preguntas, todas con explicación y 41 con imagen. Quedan los pasos 1–5: exponer versión en la API, escribir Room, reducir CompetencyData a contenido de arranque y unificar el catálogo. |

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
| Iconografía Material sin emojis | Toda la interfaz de la app. Verificado con un escáner contra los AAR reales. |
| Pantalla de resultados rehecha | Faltaba la llamada a `loadData()`, por eso no salían competencia ni nivel. |
| Progreso: parpadeo del estado vacío | El «cargando» se retiraba al llegar las estadísticas, sin esperar a las competencias. |
| Contenedores de error en rojo | `errorContainer` apuntaba a los verdes de éxito en los dos temas. |
| TODO-A · Umbral de aprobación al 70 % | `domain/LevelRules.kt` como valor único. Verificado en dispositivo. Hoy no altera el juego porque las sesiones son de 5 preguntas. |
| TODO-4 · Esqueleto de carga | Contraste de 12,63:1 a 1,22:1 y esqueleto por sección con umbral de 350 ms. El ranking lleva su propio estado y su propia tarjeta de fallo. |
| «Tiempo» de Progreso pasa a ser por día | Se corrige al leer, comparando contra `lastPracticeDate`; no hace falta vigilar el cambio de día. La etiqueta pasa a «Tiempo hoy». Incluye el arreglo de una regresión propia: un leer-modificar-escribir leía de la caché. |
| Arranque en frío: fondo que sigue al modo oscuro | `windowBackground` desde `@color/fondo_arranque`, con variante en `values-night/`. Sigue al modo del sistema, no al conmutador de Perfil. |
| TODO-17 · Catálogo de logros unificado y visible en el panel | Mandan las seis de la rejilla de Perfil, con dos peldaños nuevos de racha (7 y 15 días), en dos filas de tres. El panel muestra las mismas: `max_streak_days` viaja en la sincronización (modelo, migración 0003 y serializador). |
| TODO-16 · Los logros se perdían al perder la racha | No se guardaban en ninguna parte: se recalculaban desde los contadores vivos. Dos columnas de máximo histórico en `user_stats` y la primera migración no destructiva del proyecto. Verificado: datos intactos y «Constancia» desbloqueada con la racha en 0. |
| TODO-12 · R8 rompía toda la red, solo en release | El modo completo de R8 borraba el argumento de tipo del `Continuation`, y Retrofit no podía deducir qué deserializar: ninguna llamada llegaba a salir. Verificado: `POST /api/reports/sync/` 201 y ranking 200. |
| TODO-13 · La racha seguía contando días perdidos | Solo se recalculaba al escribir. Corregido al leer, como el tiempo. Verificado: pasó de «3 días» a «0 días» tras cuatro sin practicar. |
| TODO-14 · Señalar en la gráfica el día que rompió la racha | Opción A de tres: un solo día en rojo `error` con flama hueca. Verificado en los dos temas; hoy no se marca. |
| TODO-15 · La gráfica semanal agrupaba por fecha UTC | Toda práctica posterior a las 19:00 caía en el día siguiente. `'localtime'` en la consulta. Verificado: «días activos» de 4/7 a 3/7 con el mismo total semanal. |
| TODO-5 · Botón de cambio de tema (panel) | Unfold lo escondía en el desplegable de la cuenta. Ahora hay un botón de 38×38 fijo bajo la cabecera, contra el borde derecho, que cicla Sistema → Claro → Oscuro. Cuelga del bloque `messages` porque `footer` lo redefinen las vistas del admin. |
| TODO-9 · Tres defectos de estado en la UI | El proyecto no compilaba (faltaba `CatalogoCache`). Esqueleto de Inicio: la carga se pedía en el `ON_RESUME`, que dentro de un `NavHost` no llega hasta que acaba la transición. Aviso de racha y tarjeta de estadísticas naciendo en cero. Tiempo clavado en «0 seg» por un `derivedStateOf` sin dependencias. Verificado en dispositivo. |
| TODO-8 · Paleta del modo oscuro (opción B) | Azul para acción, ámbar para logro, bordes visibles, esqueleto discreto. Verificado en dispositivo. |
