# Conciliación de los dos bancos de preguntas

> **Resuelto el 29/09/2026.** El autor confirmó que **CompetencyData tiene los
> originales**, y el panel se sembró a partir de él: 41 preguntas creadas, 36
> corregidas en redacción y explicación, 17 que ya coincidían. El panel pasó de
> 60 a **101** preguntas y ahora contiene las 94 originales más 7 que solo
> existían en él y se conservaron.
>
> Lo de abajo es el informe regenerado después de sembrar, y por eso ya no
> muestra diferencias: queda como registro del método y para volver a correrlo
> si los dos bancos se separan otra vez.

## Resumen por nivel

| Nivel (app) | Nivel (Django) | Nombre | En la app | En Django | Diferencia |
| --- | --- | --- | --- | --- | --- |
| 101 | 1 | Nivel 1 – Comprensión literal | 6 | 6 |  |
| 102 | 2 | Nivel 2 – Interpretación e inferencia | 13 | 13 |  |
| 103 | 3 | Nivel 3 – Análisis crítico y evaluación | 7 | 7 |  |
| 201 | 4 | Interpretación | 9 | 10 | +1 |
| 202 | 5 | Argumentación | 10 | 12 | +2 |
| 203 | 6 | Formulación y ejecución | 6 | 7 | +1 |
| 301 | 7 | Feelings | 5 | 5 |  |
| 302 | 8 | Complete the Conversations | 5 | 5 |  |
| 303 | 9 | Complete the text | 8 | 8 |  |
| 304 | 10 | Reading Comprehension | 7 | 7 |  |
| 401 | 11 | Nivel 1 – Conocimiento Constitucional | 6 | 8 | +2 |
| 402 | 12 | Nivel 2 – Análisis de Perspectivas | 6 | 6 |  |
| 403 | 13 | Nivel 3 – Análisis Crítico | 6 | 7 | +1 |
| | | **Total** | **94** | **101** | **+7** |

La columna «Diferencia» en negrita marca los niveles donde el panel tiene
**menos** preguntas que la app: ahí es donde el estudiante perdería contenido.

> Cinco niveles del panel tienen menos de 5 preguntas, que es el tamaño de una
> sesión. `calculateQuestionCount()` recorta al total disponible, así que esos
> niveles se jugarían con 3 o 4 preguntas — y con el umbral del 70 %, un nivel
> de 3 exige acertar las 3 para aprobar.

## Qué hay que decidir en cada nivel

### Nivel 201 → Django 4 · Interpretación

**Misma pregunta, distinta redacción (2)** — hay que elegir una:

- *Panel:* Camilo quiere inscribirse a clases de pilates y escoger el total de sesiones mensual donde el costo por sesión sea menor. Camilo elige 2 sesiones por 
  *App:* Camilo quiere inscribirse a las clases de pilates ofrecidas por el instructor y escoger el total de sesiones mensual en la que el costo por sesión sea
- *Panel:* Patricia está muy contenta, pues afirma que, de la forma en que su tía repartió el dinero de sus bienes, ella obtendrá más dinero que si la herencia s
  *App:* Patricia está muy contenta, pues afirma que, de la forma en que su tía repartió el dinero de sus bienes, ella obtendrá más dinero que si la herencia s

### Nivel 202 → Django 5 · Argumentación

**Solo en el panel (2)** — se ganan al hacer el cambio:

- Si se realiza una campaña de reciclaje durante 20 días recolectando 2 toneladas diarias de papel y cartón, ¿cuántos litros de agua se podrían ahorrar?
- Durante la inversión en seguridad vial 1996-2002, los años con mayor inversión fueron:

**Misma pregunta, distinta redacción (5)** — hay que elegir una:

- *Panel:* Una persona afirma:

"Como al día se ahorran 140 litros de petróleo por cada tonelada de papel y cartón reciclado en la ciudad, durante un mes se ahor
  *App:* Una persona afirma:\n\n\"Como al día se ahorran 140 litros de petróleo por cada tonelada de papel y cartón reciclado en la ciudad, durante un mes se a
- *Panel:* La inversión en seguridad se realiza el 10 de enero de cada año. En enero 10 de 2002, un euro equivalía a 2.800 pesos colombianos, aproximadamente. Se
  *App:* La inversión en seguridad se realiza el 10 de enero de cada año. En enero 10 de 2002, un euro equivalía a 2.800 pesos colombianos, aproximadamente. Se
- *Panel:* Se realizó una campaña de reciclaje durante tres días en una unidad residencial, en la que se recogieron 2 toneladas diarias de papel y cartón; por ta
  *App:* Se realizó una campaña de reciclaje durante tres días en una unidad residencial, en la que se recogieron 2 toneladas diarias de papel y cartón; por ta
- *Panel:* Al analizar los resultados, el científico afirma que la relación entre cada tiempo de las actividades del ave 1 y del ave 5 es 3:2.

La afirmación del
  *App:* Al analizar los resultados, el científico afirma que la relación entre cada tiempo de las actividades del ave 1 y del ave 5 es 3:2.\n\nLa afirmación d
- *Panel:* El científico quiere identificar cuál de las aves presenta las características de la siguiente descripción:

- Tarda el doble del tiempo en alimentars
  *App:* El científico quiere identificar cuál de las aves presenta las características de la siguiente descripción:\n\n- Tarda el doble del tiempo en alimenta

### Nivel 203 → Django 6 · Formulación y ejecución

**Solo en el panel (1)** — se ganan al hacer el cambio:

- Una pista marcada en un extremo con el número 24, en el extremo opuesto está marcada con el número:

**Misma pregunta, distinta redacción (1)** — hay que elegir una:

- *Panel:* El organizador de la fiesta quiere estimar cuál es la capacidad de la fuente, para lo cual mide la altura y el radio del recipiente en el nivel inferi
  *App:* El organizador de la fiesta quiere estimar cuál es la capacidad de la fuente, para lo cual mide la altura y el radio del recipiente en el nivel inferi

### Nivel 401 → Django 11 · Nivel 1 – Conocimiento Constitucional

**Solo en el panel (2)** — se ganan al hacer el cambio:

- ¿Por qué el proyecto que condena el satanismo por ser contrario a las creencias de la mayoría no podría aprobarse?
- Una colombiana devota del islam lleva pañoleta en la cabeza. En una entrevista para un cargo público, le advierten que no puede tomar el trabajo si no

### Nivel 403 → Django 13 · Nivel 3 – Análisis Crítico

**Misma pregunta, distinta redacción (1)** — hay que elegir una:

- *Panel:* ¿Cuál es un argumento válido para contradecir la postura de que los policías de tránsito causan las congestiones vehiculares?
  *App:* ¿Cuál de los siguientes es un argumento válido para contradecir la postura expuesta?

