# Historial de cambios

## [Sin publicar]

- **Se retira el banco de pictogramas de ARASAAC.** ARASAAC ha confirmado por
  escrito que su licencia CC BY-NC-SA no permite el uso con un modelo comercial
  (suscripción, licencias de centro, funciones de pago), que la finalidad
  educativa no exime, que no hay licencia comercial ni forma de solicitarla, y
  que da igual acceder por la API. Como el proyecto contempla comercializarse,
  se quita la función ahora para no tener que retirarla más adelante ni dejar
  materiales de usuarios con pictogramas sujetos a esa licencia.
  - Fuera: `core/pictogramas.py`, la opción `--pictogramas` de `cli.py`, la
    casilla en la pestaña Formato y la línea de pictogramas de la hoja de
    registro.
  - El perfil «TEL/TDL (apoyo visual)» pasa a llamarse «TEL/TDL» (mantiene el
    formato: Arial 15, interlineado 1,8, márgenes amplios, pasos numerados).

## [1.7.0] — 2026-09-07

- **Nueva pestaña «Adaptación curricular (ACIS)»** (en pruebas): genera un
  borrador del Anexo III.b (adaptación curricular individualizada y
  significativa) de ESO para copiarlo en Raíces.
  - Se adjuntan dos programaciones didácticas (.docx): la de la materia y la
    del curso al que se adapta. La app lee la del curso destino y vuelca sus
    criterios de evaluación, contenidos e instrumentos como punto de partida
    editable (ya están a ese nivel).
  - **Perfil de accesibilidad**: como referencia mientras se edita, un atajo
    por categoría de necesidad educativa que se despliega en necesidades
    funcionales no clínicas (`core/acis.json`, editable).
  - Casilla «el equipo de orientación ha determinado ACS para esta materia»;
    si no se marca, se avisa y el bloque de la materia no se genera.
  - Los apartados vacíos salen como «[PENDIENTE — lo determina el equipo
    docente]»; el documento sale marcado como BORRADOR y se genera en local
    (no se envía a ningún servicio). Sin bloque de firmas.
  - `core/acis.py`, `core/acis.json`, `core/programacion.py`, `core/acis_ia.py`
    (adaptación con IA, aún sin conectar en la ventana), `crear_acis.py`.
- Pruebas nuevas: `prueba_acis.py`, `prueba_programacion.py`,
  `prueba_acis_ia.py`.

## [1.6.0] — 2026-09-06

- **Hoja interna de registro de adaptaciones**, casilla en la pestaña Formato:
  al adaptar un documento, genera junto a él un archivo «— registro.docx» que
  recoge qué ajustes de formato y de contenido se han aplicado y el marco
  normativo (Decreto 23/2023 art. 23; Orden 1712/2023 art. 10.3.b/c; Orden
  130/2023 art. 17.1). Es un documento de trabajo del profesorado: no
  sustituye a los anexos oficiales del expediente y no incluye datos del
  alumnado (deja un hueco para rellenar a mano).
- Los textos y plantillas del registro están en `core/registro.json`,
  editables sin tocar el código.
- `cli.py`: opción `--registro`.
- La numeración de pasos al «separar procedimientos» ahora reinicia en 1 en
  cada actividad, en vez de continuar la numeración global.

## [1.5.0] — 2026-09-05

- **Dividir preguntas compuestas** (con IA), en la pestaña «Contenido con IA»:
  las preguntas largas o que piden varias cosas a la vez se dividen en varias
  preguntas más cortas y consecutivas, sin añadir nada ni responderlas. Se
  puede combinar con «Numerar preguntas» (sin IA, ya existente) para
  renumerar el resultado.
- `cli.py`: nueva tarea `dividir_preguntas` para `--ia`.

## [1.4.0] — 2026-09-05

- **Numerar preguntas**, en la pestaña Formato: casilla que renumera de forma
  clara y consecutiva los párrafos detectados como preguntas (terminan en
  «?»), aplicándoles el estilo de lista numerada.
- **Espacio para responder**, en la pestaña Formato: campo numérico con la
  cantidad fija de líneas en blanco que se insertan después de cada pregunta
  detectada, para que el alumnado tenga sitio donde escribir la respuesta.
- `cli.py`: opciones `--numerar-preguntas` y `--espacio-respuestas N`.
- Sin cambios en la adaptación de contenido con IA.

## [1.3.1] — 2026-09-04

- **Cambio de empaquetado para evitar el falso positivo de antivirus.** Hasta la
  1.3.0 se distribuía como un único `.exe` (`--onefile`), que Windows Defender
  marcaba por error como `Trojan:Win32/Wacatac.B!ml` y ponía en cuarentena al
  descargarlo. Ahora se distribuye como:
  - `AdaptadocsSetup.exe` — instalador (Inno Setup), con acceso directo.
  - `Adaptadocs-portable.zip` — carpeta lista para usar sin instalar.
  Ambos pasan el análisis de Defender sin avisos.
- Sin cambios de funcionamiento respecto a la 1.3.0.

## [1.3.0] — 2026-09-04

- **Banco de pictogramas (ARASAAC)** en la pestaña Formato: casilla que añade
  al final del documento una tabla «palabra + pictograma» con las palabras de
  «Resaltar palabras». Requiere conexión; envía a ARASAAC solo esas palabras.
  Incluye la atribución (CC BY-NC-SA, Sergio Palao, Gobierno de Aragón).
- Nuevo perfil **«TEL/TDL (apoyo visual)»**, con el banco de pictogramas
  activado.
- `cli.py`: opción `--pictogramas`.
- `core/pictogramas.py`: cliente de la API de ARASAAC con caché en disco.

## [1.2.0] — 2026-09-04

- **Separar procedimientos en pasos numerados sin IA**, en la pestaña Formato:
  desplegable «No separar» / «Solo los marcados con PASOS:» / «Detectar
  automáticamente». Trocea el párrafo por frases y por conectores de secuencia
  y le aplica el estilo de lista numerada; no reescribe el texto.
- `cli.py`: opción `--separar-pasos {no,marcados,auto}`.
- La antigua casilla «Convertir viñetas en lista numerada» se renombra a
  «Numerar las listas con viñetas» (misma función).

## [1.1.1] — 2026-09-04

- El proyecto pasa a llamarse **Adaptadocs** (antes «Adaptador de documentos
  Word»). El ejecutable ahora es `Adaptadocs.exe`. Repositorio movido a
  `Utopikamente/adaptadocs` (GitHub mantiene la redirección desde el anterior).
- Sin cambios de funcionamiento respecto a la 1.1.0.

## [1.1.0] — 2026-09-04

Adaptación de **contenido con IA** (opcional, funciones "Pro").

- Nueva pestaña «Contenido con IA» en la ventana.
- Simplificación del texto a un nivel de lectura configurable (1º Primaria … 2º
  ESO, Lectura Fácil).
- Conversión de procedimientos en pasos numerados.
- Glosario de términos difíciles (al final).
- Resumen por apartados (al principio).
- Preguntas de comprensión (al final), número configurable.
- Elección de modelo: Opus 5 / Sonnet 5 / Haiku 4.5.
- La clave de API se guarda en el Administrador de credenciales de Windows.
- Aviso claro de que el texto se envía a Anthropic al usar la IA.
- `cli.py`: opciones `--ia`, `--nivel`, `--modelo-ia`, `--preguntas`.
- Comprobaciones nuevas: `prueba_ia.py` (sin red) y `prueba_ia_api.py` (real).

## [1.0.0] — 2026-09-04

Primera versión.

- Ventana de escritorio (Tkinter) para adaptar documentos `.docx`.
- Perfiles: General, Dislexia, TDAH, TEA, Discapacidad intelectual leve, Baja visión.
- Ajustes de formato: fuente, tamaño, interlineado, espacio entre párrafos,
  alineación a la izquierda, márgenes amplios, una sola columna, alto contraste,
  títulos en negrita, viñetas convertidas en lista numerada.
- Resaltado de palabras clave con color a elegir.
- Uso por línea de comandos y por lotes (`cli.py`).
- Ejecutable de Windows generado con PyInstaller.
