# Proyecto: adaptador de materiales educativos

> Este archivo son instrucciones vinculantes para trabajar en este repositorio.
> Sustituye/amplía el enfoque anterior (Adaptadocs, adaptación de formato). A
> partir de aquí, Adaptadocs pasa a ser **la capa de formato** dentro de un
> proyecto más amplio: adaptar materiales y proponer adaptaciones curriculares
> a partir del **perfil de barreras y apoyos** de un alumno.

## Qué es esto

Herramienta para profesorado que adapta documentos y exámenes al perfil de
necesidades de un alumno, y (más adelante) genera propuestas de adaptación
curricular significativa.

El autor trabaja en un centro educativo y aporta el criterio profesional. Su
nivel de Python es básico: explica los cambios en lenguaje claro y evita
soluciones que no pueda mantener.

## Contexto profesional: no inventar

Si hace falta un criterio pedagógico que no esté escrito en este archivo,
**preguntar antes de implementarlo**. No deducir qué apoyos corresponden a qué
barrera, ni qué formato tiene un documento oficial. Este dominio tiene
normativa y práctica establecida, y una suposición razonable puede ser
profesionalmente incorrecta.

Comunidad autónoma de referencia: **Madrid**. Etapas cubiertas: **Primaria y
ESO**.

### Normativa de referencia (adjuntada y ya leída por Claude)

- **Decreto 23/2023**, de 22 de marzo (BOCM núm. 71, 24/03/2023): regula la
  atención educativa a las diferencias individuales del alumnado en la
  Comunidad de Madrid. Es la norma **transversal** (Infantil/Primaria/ESO):
  define barreras, necesidades educativas, el informe psicopedagógico (anexo
  I) y el dictamen de escolarización (anexo II).
- **Orden 1712/2023**, de la Vicepresidencia, Consejería de Educación y
  Universidades: organización, funcionamiento y evaluación en **ESO**
  (capítulo III, artículos 8 a 18, es la sección de atención a las diferencias
  individuales).
- **Orden 130/2023**, de 23 de enero: organización, funcionamiento y
  evaluación en **Educación Primaria** (capítulo III, artículos 10 a 17).

Cuando el código o los datos citen un apoyo o una regla, deben citar el
artículo de una de estas tres normas. Si una regla no tiene cita, es una
suposición y hay que confirmarla con el autor antes de usarla.

## Reglas duras (no negociables)

- Nunca se almacenan datos identificativos de alumnos: ni nombre, ni
  expediente, ni fecha de nacimiento, ni diagnóstico clínico. El perfil
  describe barreras y apoyos, no personas.
- El programa **no almacena** diagnósticos, informes clínicos ni el informe
  psicopedagógico. Para ajustar una adaptación puede ofrecerse un **perfil de
  accesibilidad**: el docente elige, como atajo, una categoría de necesidad
  educativa (p. ej. TEA, TDL, discapacidad intelectual leve) que se
  **despliega en una lista editable de necesidades funcionales no clínicas**
  (p. ej. «necesita lenguaje literal», «necesita mucha repetición»). Solo esas
  necesidades funcionales —no la etiqueta clínica en bruto— se usan en los
  prompts. La correspondencia categoría → necesidades vive en un archivo de
  datos local editable y no se envía a ningún servicio. Nada de esto se guarda
  entre sesiones. Un campo que persista un diagnóstico sigue siendo un error:
  avisar.
- El documento de ACIS que genera el programa (que puede llevar el nombre del
  alumno cuando lo rellena el docente) **nunca se envía a la IA ni a ningún
  servicio externo**: se genera en local y el docente lo copia en Raíces. A la
  IA solo van la programación de la materia (sin datos personales), el nivel
  de competencia curricular objetivo y el perfil de accesibilidad funcional.
- La herramienta propone, el profesional decide. Ninguna salida se presenta
  como definitiva. Todo documento generado es editable y requiere validación
  humana antes de usarse.
- Las reglas pedagógicas viven en archivos de datos editables (JSON o YAML),
  nunca dentro del código ni dentro de los prompts. El autor debe poder
  cambiarlas sin programar.
- Cuando el sistema no sepa resolver algo, debe decirlo en la salida, no
  rellenar el hueco. Un aviso de "esto requiere decisión profesional" es una
  función del producto, no un fallo.

### La distinción legal más importante (no obvia, confirmada en la normativa)

La **adaptación curricular significativa (ACS/ACIS)** — la que cambia
criterios de evaluación y puede coger contenidos de cursos anteriores — está
**legalmente reservada** al alumnado con **necesidades educativas especiales**
en el sentido estricto del artículo 10 del Decreto 23/2023: discapacidad
(intelectual, motora, auditiva, visual), TEA, trastornos graves de la
comunicación/lenguaje, trastornos graves de conducta, pluridiscapacidad o
retraso general del desarrollo (<5 años).

Para el resto de necesidades específicas (TDAH, dificultades de aprendizaje
tipo dislexia/discalculia, retraso madurativo) la normativa **solo permite la
adaptación curricular NO significativa** (mover contenidos de la unidad
anterior dentro del mismo ciclo, sin tocar los criterios de evaluación del
ciclo — Decreto 23/2023 arts. 21 y 23.3; Orden Primaria art. 12.2.b y 17.3;
Orden ESO art. 16), más medidas de acceso a la evaluación (tiempo, formato,
lectura en voz alta, apoyo PT/AL condicionado a desfase curricular
significativo).

**Consecuencia para el diseño:** la herramienta no puede inferir si un alumno
tiene derecho a ACS a partir de la descripción de sus barreras. Esa
clasificación la determina el equipo de orientación mediante evaluación
psicopedagógica (documento que la herramienta no almacena). El sistema debe
pedir un dato no clínico equivalente — p. ej. una casilla «el equipo de
orientación ha determinado adaptación curricular significativa: sí/no», por
materia — y bloquear la vía ACS si no está marcada, explicando por qué.

## Modelo de perfil

Un perfil describe barreras y apoyos, organizados según los tres principios
del DUA. Es reutilizable entre alumnos con necesidades parecidas.

### Representación (cómo accede a la información)

Ejemplos orientativos, ahora con base normativa donde la hay:

- Dificultad en comprensión lectora
- Requiere apoyo visual complementario (Decreto 23/2023 art. 12.c, art. 23.1;
  Orden Primaria art. 17.1: tipos y tamaños de fuente adaptados)
- Dificultad con lenguaje figurado o enunciados largos → lectura en voz alta
  de las cuestiones planteadas (Orden ESO art. 16.c)

### Acción y expresión (cómo demuestra lo que sabe)

- Dificultad al escribir → instrumentos de evaluación diversos / medios
  alternativos de comunicación (Decreto 23/2023 art. 10.3.e para discapacidad;
  adecuación general de instrumentos en Decreto 23/2023 art. 23.1)

### Implicación (cómo se mantiene en la tarea)

**[COMPLETAR — pendiente]**. La normativa revisada regula organización y
evaluación, no una taxonomía DUA de motivación/implicación. No se ha
encontrado base citable aquí: pendiente de que el autor aporte criterio
propio, o de acordar si se investiga con fuentes DUA/CAST generales (no
específicas de Madrid) como punto de partida editable.

## Nivel de competencia curricular

Se indica por materia o por competencia específica, no como un curso global.
Procede de la evaluación psicopedagógica; la herramienta nunca lo determina
por su cuenta.

## Reglas de adaptación: barrera → apoyo

**Borrador inicial, sin validar por el autor todavía** (ver conversación):

| Barrera (redacción no clínica) | Apoyos que se aplican | Base normativa | Notas / prioridad |
|---|---|---|---|
| Necesita más tiempo para completar pruebas escritas | Ampliar tiempo (hasta +35 % en Primaria) | Orden Primaria art. 17.1; Orden ESO art. 16.c | Compatible con cualquier otro apoyo |
| Dificultad para leer enunciados largos o con lenguaje complejo | Lectura en voz alta de las preguntas por el profesorado | Orden ESO art. 16.c | En Primaria, análogo dentro de «adaptación de formatos» |
| Necesita apoyo visual complementario al texto | Tipografía/tamaño adaptado, materiales visuales | Decreto 23/2023 art. 12.c y 23.1; Orden Primaria art. 17.1 | — |
| Dificultad para expresarse por escrito | Instrumentos de evaluación alternativos (oral, medios alternativos) | Decreto 23/2023 art. 10.3.e; Orden ESO art. 16.c | — |
| Desfase curricular ≥2 cursos y deterioro funcional muy significativo, **con ACS determinada por orientación** | Adaptación curricular SIGNIFICATIVA por materia + apoyo PT/AL | Decreto 23/2023 art. 12.a/b; Orden ESO art. 10.3.a/d | Solo si la casilla de ACS está marcada; si no, avisar y no ofrecerla |
| Desfase curricular dentro del mismo ciclo, sin llegar a lo anterior | Adaptación curricular NO significativa (mover contenidos de la unidad anterior del mismo ciclo) | Decreto 23/2023 arts. 21 y 23.3; Orden Primaria art. 12.2.b y 17.3 | No cambia criterios de evaluación del ciclo |

**Conflictos conocidos a resolver:** [COMPLETAR — pendiente de validar con el
autor cuáles son reales en la práctica; el más importante ya identificado es
el límite legal ACS/ACNS de arriba].

## Convenciones de trabajo

- Cambios pequeños y de uno en uno. Nada de refactorizaciones amplias sin
  pedirlo.
- Antes de un cambio que toque varios archivos, explicar qué se va a hacer y
  esperar confirmación.
- Toda función nueva lleva su test. Los tests deben poder leerse y entenderse
  sin saber Python a fondo.
- Después de cada cambio, resumir en dos frases qué cambió y qué podría
  romperse.
- Commits pequeños y frecuentes, con mensajes en español.

## Glosario

- **ACS**: adaptación curricular significativa. Modifica los criterios de
  evaluación. La decide el equipo docente con orientación. Legalmente
  reservada a necesidades educativas especiales (art. 10 Decreto 23/2023).
- **ACNS**: adaptación no significativa. Mantiene los criterios; cambia el
  acceso, el formato o el andamiaje.
- **NEAE**: necesidades específicas de apoyo educativo.
- **NEE**: necesidades educativas especiales (subconjunto de NEAE, art. 10
  Decreto 23/2023: discapacidad, TEA, trastornos graves de conducta/lenguaje,
  pluridiscapacidad, retraso general del desarrollo).
- **PT / AL**: pedagogía terapéutica / audición y lenguaje.
- **DUA**: diseño universal para el aprendizaje.
