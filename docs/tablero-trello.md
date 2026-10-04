# Tablero Kanban — «Trabajo de grado»

Contenido listo para volcar en Trello (https://trello.com/b/E0s3m3iw/trabajo-de-grado).
Cuatro columnas, las que fija la Fase 4 del anteproyecto.

> **Fecha límite 22 de octubre de 2026** (reunión con el profesor, 30/09/2026). La
> directiva es pulir la experiencia, no poblar la base: se trabaja con las 101
> preguntas que ya hay y se deja todo listo para cargar contenido después de
> validar la app con estudiantes.

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
| TODO-21 · Música, sonidos y vibración | Música de menú y de nivel, acierto y error, vibración. No hay ni un recurso de audio en el proyecto: hay que conseguirlos con licencia libre y documentarla. Conmutador en Perfil, respeto al silencio del sistema, pausa en segundo plano. |
| TODO-20 · Acortar los textos de Lectura Crítica | Las 9 preguntas más largas del banco son todas de ahí; el nivel 2 promedia 1 201 caracteres frente a 340–557 del resto. Unas 20 preguntas, trabajo editorial en el panel. El pasaje no se puede recortar sin destruir el ejercicio: lo que no baje se resuelve con TODO-24 y TODO-22. **Además, dos pasajes truncados:** las preguntas `id 5` y `id 6` de Lectura Crítica 1 cortan a mitad de frase, antes de la información que hace falta para responder. Es defecto del dato en el panel, no de la app. |
| TODO-2 · Carga de preguntas amigable | Las cartillas llegan en PDF con imágenes. Los tres caminos actuales (formulario, CSV, script) no sirven para quien no es desarrollador. |
| TODO-6 · Estadísticos y explorador | Moda de competencias, media por programa y competencia, y un gráfico filtrable por programa × competencia × nivel × fechas. |
| TODO-7 · Animaciones de Material Design | Transiciones entre pantallas, entrada de listas, feedback de acierto y error. La respuesta al pulsar ya está hecha en la barra de navegación (25/09/2026). |
| TODO-18 · Los ids de pregunta cambiaron bajo los intentos | Los intentos apuntan a los ids de `CompetencyData` (1001+) y el banco ahora trae los de Django (1..101). La priorización de lo fallado deja de funcionar en silencio. Tres salidas posibles, ninguna aplicada. **Baja de prioridad (30/09/2026):** el piloto usará cuentas nuevas, que nacen sin historial. Sigue afectando a la cuenta de pruebas, así que hay que resolverlo antes de una demo en vivo. |

## En progreso

| Tarjeta | Descripción |
| --- | --- |
| TODO-22 · Nivel de práctica antes del básico | **Mecanismo escrito, sin compilar.** `order = 0` en el panel → ids 100/200/300/400, y `LevelRules.esDePractica` como única regla. Hizo falta una migración de Room: el catálogo solo se siembra en la primera instalación, así que en un teléfono con la app ya puesta los niveles nuevos no aparecerían nunca. Interfaz: opción B, secciones «Practica» y «Evalúate». La app solo enseña el nivel si tiene preguntas, así que poblarlo después no pide versión nueva. Faltan la retroalimentación inmediata, el contenido y verificar en dispositivo. |
| TODO-B · Comunicación Escrita, quinta competencia | Requerimiento de Desarrollo Estudiantil. Un nivel con las 10 preguntas del `.docx`, opción múltiple. Diverge del anteproyecto (que la ponía dentro de Lectura Crítica) con acuerdo del profesor: **hay que reflejarlo en la memoria**. Hizo falta migración de Room, los dos builders, el mapeo de sincronización y una tercera lista escrita a mano que se me pasó. Verificado: 18 niveles y 111 preguntas. |
| TODO-26 · Práctica como modo, con retroalimentación inmediata | Cada nivel se juega practicando o evaluándose. Practicar no registra intentos, no mueve el porcentaje y no desbloquea, pero sí suma tiempo y racha, y está disponible en niveles bloqueados. Al responder en práctica se tiñen las opciones y aparece el porqué debajo, con desplazamiento automático porque con preguntas largas nacía fuera de pantalla. En evaluación no se enseña nada: la explicación se guarda para el repaso de resultados. Verificado en dispositivo por los dos lados. Faltan «unir» y «arrastrar». |
| TODO-27 · Verde del veredicto y unir parejas | Material 3 no tiene rol de éxito, así que el verde se expone con un `CompositionLocal` que provee `Reta2Theme` (no `isSystemInDarkTheme()`: la app tiene conmutador propio). Contrastes 4,56:1 y 6,20:1, AA en los dos temas. Unir parejas en disposición B, sin datos nuevos: las 5 preguntas de Feelings ya comparten las 8 opciones. Hizo falta llevar `formato_practica` del panel a Room (migración 14), y un `Level` construido a mano que perdía el campo por el camino. Verificado: 0 intentos, nada desbloqueado, tiempo y racha sí. |
| TODO-28 · Completar el texto arrastrando | Disposición A: una frase por línea, banco abajo, se coloca todo y se comprueba de golpe. Se descartó el pasaje continuo porque la diana quedaba por debajo de 48 dp y porque nada en los datos une una pregunta con su número de hueco. Arrastre hecho a mano con límites en coordenadas de la raíz, y también se puede tocar (el dedo tapa la diana, y con lector de pantalla no se arrastra). Verificado sobre un nivel bloqueado: 6/8, 0 intentos, nada desbloqueado, tiempo, preguntas y racha sí. |
| TODO-29 · «Continuar practicando» ignoraba la práctica | Filtraba por progreso, y el progreso sale de los intentos acertados que la práctica no registra: la sección enseñaba una competencia vieja mientras el estudiante practicaba otras. Marca `last_practiced_at` por nivel, escrita al abrir en los dos modos. Segundo fallo encadenado: la caché del catálogo solo se invalidaba al escribir progreso, así que la marca quedaba guardada y la pantalla no se enteraba. Verificado en dispositivo. |
| TODO-30 · Contextos truncados | Dos problemas con el mismo síntoma. **Datos:** cinco pasajes de Lectura Crítica entraron cortados porque en `CompetencyData` se concatenan con `+` y la siembra leyó solo el primer trozo (151 car donde había 2 090). Reparados emparejando por prefijo con un analizador de literales de Kotlin. **Interfaz:** en Competencias Ciudadanas no había dato roto; la vista previa recortaba a 150 caracteres antes que el `maxLines` del componente y hacía parecer incompleto lo que no lo estaba. Verificado en dispositivo. |
| TODO-3 · Imagen de contexto como archivo | **Lado Django hecho:** modelo `ContextAsset` con `ImageField`, `MEDIA_*`, subida con vista previa en el admin, URL absoluta en la API, y las 12 imágenes migradas desde `res/drawable` con 41 preguntas enlazadas. Falta el lado Android: Room, Coil y quitar `getIdentifier()`. |
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
| El heatmap no seguía al cambio de tema | `isDark` se leía una sola vez y `cal.paint()` corría una sola vez. Ahora repinta con un `MutationObserver` sobre la clase del `<html>`. Sin verificar en pantalla: el CDN de cal-heatmap está bloqueado en el navegador de pruebas. |
| TODO-19 · Progreso al 137 % y dos avisos que mentían | El numerador contaba intentos de preguntas que ya no existen. Acotado al banco en los tres cálculos. Además: el mensaje del umbral al repetir un nivel superado, y «Imagen no encontrada» en preguntas sin imagen. |
| TODO-25 · Imágenes que no parezcan pantallazos | Las 12 eran tres cosas distintas. Las figuras se despegan del papel —luminancia como matiz alfa, fondo transparente, recorte al contenido— y la app las tiñe con el color del tema, así que no hay caja blanca en ninguno. Lo hace el panel al guardar, no un guion suelto. **Y salió algo peor que el estilo:** el «contexto» de siete preguntas de Inglés contenía las respuestas; el pasaje real estaba dentro del `.webp`. Corregido, con copia de seguridad. Verificado en dispositivo y en los dos temas. |
| TODO-24 · El texto completo hasta arriba | Opción B de tres: dos alturas. El tope `fillMaxHeight(0.7f)` impedía que la hoja subiera aunque se arrastrase — el «3/4 de pantalla» que señaló el profesor. Incluye el inset de la barra de estado, que dejaba el tirador entre el reloj y la batería, y la retirada del botón «Cerrar» redundante. Verificado en dispositivo y en los dos temas. Queda sin comprobar el desplazamiento con un pasaje muy largo. |
| TODO-23 · Retroalimentación con la explicación | En evaluación va solo al final, en resultados; el inmediato queda para práctica (TODO-22). Hizo falta `RepasoDeSesion`: a resultados solo llegaban escalares por la ruta y el estado borraba la opción elegida. Interfaz: opción A de tres, lista plegable con los fallos abiertos. Incluye el arreglo de un `clickable` sin indicación explícita que tumbaba la pantalla. Verificado en dispositivo en los dos temas, con las letras contrastadas contra Room. |
| TODO-17 · Catálogo de logros unificado y visible en el panel | Mandan las seis de la rejilla de Perfil, con dos peldaños nuevos de racha (7 y 15 días), en dos filas de tres. El panel muestra las mismas: `max_streak_days` viaja en la sincronización (modelo, migración 0003 y serializador). |
| TODO-16 · Los logros se perdían al perder la racha | No se guardaban en ninguna parte: se recalculaban desde los contadores vivos. Dos columnas de máximo histórico en `user_stats` y la primera migración no destructiva del proyecto. Verificado: datos intactos y «Constancia» desbloqueada con la racha en 0. |
| TODO-12 · R8 rompía toda la red, solo en release | El modo completo de R8 borraba el argumento de tipo del `Continuation`, y Retrofit no podía deducir qué deserializar: ninguna llamada llegaba a salir. Verificado: `POST /api/reports/sync/` 201 y ranking 200. |
| TODO-13 · La racha seguía contando días perdidos | Solo se recalculaba al escribir. Corregido al leer, como el tiempo. Verificado: pasó de «3 días» a «0 días» tras cuatro sin practicar. |
| TODO-14 · Señalar en la gráfica el día que rompió la racha | Opción A de tres: un solo día en rojo `error` con flama hueca. Verificado en los dos temas; hoy no se marca. |
| TODO-15 · La gráfica semanal agrupaba por fecha UTC | Toda práctica posterior a las 19:00 caía en el día siguiente. `'localtime'` en la consulta. Verificado: «días activos» de 4/7 a 3/7 con el mismo total semanal. |
| TODO-5 · Botón de cambio de tema (panel) | Unfold lo escondía en el desplegable de la cuenta. Ahora hay un botón de 38×38 fijo bajo la cabecera, contra el borde derecho, que cicla Sistema → Claro → Oscuro. Cuelga del bloque `messages` porque `footer` lo redefinen las vistas del admin. |
| TODO-9 · Tres defectos de estado en la UI | El proyecto no compilaba (faltaba `CatalogoCache`). Esqueleto de Inicio: la carga se pedía en el `ON_RESUME`, que dentro de un `NavHost` no llega hasta que acaba la transición. Aviso de racha y tarjeta de estadísticas naciendo en cero. Tiempo clavado en «0 seg» por un `derivedStateOf` sin dependencias. Verificado en dispositivo. |
| El tamaño de sesión se queda en 5 | Decidido en la reunión del 30/09/2026: la objeción del profesor es de *microlearning*, sesiones cortas. `calculateQuestionCount()` no cambia. Efecto secundario a declarar en la memoria: el umbral del 70 % sigue siendo 4 de 5. |
| TODO-8 · Paleta del modo oscuro (opción B) | Azul para acción, ámbar para logro, bordes visibles, esqueleto discreto. Verificado en dispositivo. |
