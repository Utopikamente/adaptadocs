# Adaptadocs

[![Comprobaciones](https://github.com/Utopikamente/adaptadocs/actions/workflows/ci.yml/badge.svg)](https://github.com/Utopikamente/adaptadocs/actions/workflows/ci.yml)

Aplicación de escritorio para **transformar un documento `.docx` en otro `.docx`
adaptado**, pensada para crear materiales más accesibles para alumnado con
dificultades de aprendizaje (dislexia, TDAH, TEA, discapacidad intelectual leve,
baja visión…).

Tiene dos partes:

- **Formato y presentación** (siempre disponible, gratis, sin conexión): todo
  ocurre en tu ordenador.
- **Contenido con IA** (opcional): reescribe el texto a un nivel de lectura más
  sencillo, añade glosario, resumen y preguntas de comprensión. Necesita una
  clave de API de Anthropic y **envía el texto del documento a Claude** para
  procesarlo. Ver la sección [Adaptación de contenido con IA](#adaptación-de-contenido-con-ia-opcional).

---

## Descargar (Windows)

Dos formas, ninguna necesita permisos de administrador:

- **Portable** (recomendado): descarga
  [`Adaptadocs-portable.zip`](https://github.com/Utopikamente/adaptadocs/releases/latest/download/Adaptadocs-portable.zip),
  descomprímelo (clic derecho → *Extraer todo*) y ejecuta `Adaptadocs\Adaptadocs.exe`.
- **Instalador** (acceso directo en el menú Inicio): descarga
  [`AdaptadocsSetup.exe`](https://github.com/Utopikamente/adaptadocs/releases/latest/download/AdaptadocsSetup.exe)
  y sigue el asistente.

### Windows avisa: «editor desconocido»

Todavía **no está firmado digitalmente** (un certificado cuesta cientos de euros
al año), así que SmartScreen mostrará un aviso azul la primera vez: pulsa el
enlace **Más información → Ejecutar de todas formas**. No es un aviso de virus,
sino de que el editor no está verificado. Si Windows bloquea el instalador sin
darte esa opción: clic derecho en el archivo → **Propiedades → Desbloquear →
Aceptar**.

> Hasta la 1.3.0 se distribuía como un único `.exe`, que algunos antivirus
> marcaban por error (falso positivo típico de PyInstaller, `Wacatac.B!ml`).
> Desde la **1.3.1** se distribuye como carpeta + instalador y ese problema
> desaparece.

Para comprobar que el archivo no se ha alterado, compara su huella SHA-256 con la
del archivo `.sha256` correspondiente de la Release:

```powershell
Get-FileHash "AdaptadocsSetup.exe" -Algorithm SHA256
```

---

## Qué hace

- Cambia la **tipografía** y el **tamaño** de letra en todo el documento.
- Ajusta el **interlineado** y el **espacio entre párrafos**.
- Convierte el texto **justificado** en alineado a la izquierda.
- Amplía los **márgenes** y fuerza **una sola columna**.
- Pone el texto en **negro** (alto contraste).
- Pone los **títulos en negrita**.
- Convierte las **viñetas en una lista numerada**, opcional.
- **Separa en pasos numerados** los párrafos que describen un procedimiento
  (sin IA): solo los que marques con «PASOS:» al principio, o por detección
  automática. Trocea por frases y por conectores («luego», «después»…); no
  reescribe el texto.
- **Numera las preguntas** del documento (párrafos que terminan en «?») de
  forma clara y consecutiva, y añade una **cantidad fija de líneas en
  blanco** tras cada una para que el alumnado responda.
- **Resalta** las palabras clave que indiques, con el color que elijas.
- Respeta imágenes, tablas y la estructura de apartados del documento.
- Crea un archivo nuevo con el sufijo `(adaptado)`; **el original no se toca**.
- Opcionalmente genera una **hoja interna de registro** («— registro.docx»)
  con qué adaptaciones se han aplicado y su marco normativo (Decreto 23/2023
  art. 23; Orden 1712/2023 art. 10.3.b/c; Orden 130/2023 art. 17.1). Es un
  documento de trabajo del profesorado: **no** es el anexo oficial del
  expediente y no incluye datos del alumnado. Sus textos están en
  `core/registro.json`, editable.

Incluye **perfiles** predefinidos (General, Dislexia, TDAH, TEA, Discapacidad
intelectual leve, Baja visión, TEL/TDL) que puedes retocar antes de generar el
documento.

---

## Adaptación de contenido con IA (opcional)

En la pestaña **«Contenido con IA»** de la ventana puedes pedir, además del
formato:

- **Simplificar el texto** a un nivel de lectura (de 1º de Primaria a 2º de ESO,
  o pautas de Lectura Fácil), conservando datos, cifras y nombres propios.
- **Convertir procedimientos en pasos numerados.**
- **Dividir preguntas largas o compuestas** en varias preguntas más cortas y
  consecutivas, sin cambiar lo que preguntan.
- **Glosario** de términos difíciles, al final del documento.
- **Resumen** por apartados, al principio.
- **Preguntas de comprensión**, al final.

### Requisitos y privacidad

- Necesitas una **clave de API de Anthropic**: créala en
  <https://console.anthropic.com> → *API Keys*. Tiene coste por uso (ver abajo).
- Al usar estas funciones, **el texto del documento se envía a Anthropic
  (Claude)** por internet. Úsalo solo con materiales que no contengan datos
  personales del alumnado.
- La clave se guarda en el **Administrador de credenciales de Windows** (no en un
  archivo de texto ni en el repositorio). Puedes borrarla desde la propia app.

### Coste aproximado

Con el modelo por defecto (**Opus 5**), adaptar una ficha de 1–2 páginas con
todas las opciones cuesta del orden de **0,05–0,15 €**. Con **Sonnet 5** es
alrededor de un tercio, y con **Haiku 4.5** aún menos. Puedes elegir el modelo en
la misma pestaña.

### Por línea de comandos

```bash
setx ANTHROPIC_API_KEY "sk-ant-..."   # una sola vez (reinicia la terminal)
python cli.py ficha.docx --ia simplificar,glosario,preguntas --nivel "3º-4º de Primaria"
python cli.py ficha.docx --ia simplificar --modelo-ia claude-sonnet-5
```

---

## Adaptación curricular (ACIS)

La pestaña **«Adaptación curricular (ACIS)»** genera un borrador del **Anexo
III.b** (adaptación curricular individualizada y significativa) de la ESO en la
Comunidad de Madrid, para copiarlo después en Raíces.

- Opcionalmente se adjuntan una o dos programaciones didácticas (`.docx`): la
  de la materia y la del **curso al que se adapta**. La app las lee sin exigir
  un formato concreto (busca los títulos estándar de LOMLOE), y vuelca los
  criterios, contenidos e instrumentos del curso destino como punto de partida
  editable. Sin programación, las orientaciones se generan igual desde el
  currículo oficial.
- Un **perfil de accesibilidad** (necesidades funcionales no clínicas, con
  atajos por categoría de necesidad educativa) sirve de referencia al editar.
  Está en `core/acis.json` y se puede cambiar sin programar.
- Cada apartado muestra un panel de **Orientación** (solo lectura, no entra en
  el documento): qué pide el anexo, los criterios/contenidos del curso destino
  y, si el nivel objetivo es de Primaria, el currículo oficial de Primaria
  (Decreto 61/2022, `core/curriculo_primaria.json`), más recomendaciones de
  metodología e instrumentos según el perfil marcado.
- La ACIS está reservada al alumnado con necesidades educativas especiales cuya
  adaptación significativa haya determinado el equipo de orientación. La casilla
  correspondiente debe marcarse; si no, se avisa.
- Lo que quede vacío sale como «[PENDIENTE — lo determina el equipo docente]» y
  el documento se marca como **BORRADOR**. **Se genera en tu equipo**; no se
  envía a ningún servicio.

También por línea de comandos: `python crear_acis.py --ejemplo` crea un
`ejemplo_acis.json`, y `python crear_acis.py ejemplo_acis.json` genera el
documento.

---

## Usar desde el código fuente

Requiere **Python 3.10 o superior** (<https://www.python.org/downloads/>,
marcando *"Add python.exe to PATH"*).

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Por línea de comandos o por lotes:

```bash
python cli.py documento.docx --perfil Dislexia
python cli.py una_carpeta --perfil TDAH --resaltar "importante, recuerda, ojo"
python cli.py examen.docx --perfil Dislexia --registro   # + hoja «— registro.docx»
```

Probar rápidamente:

```bash
python crear_ejemplo.py
python cli.py ejemplo.docx --perfil Dislexia --resaltar "glucosa, oxígeno"
python prueba.py            # comprobación de formato
python prueba_ia.py         # capa de IA de contenido (sin conexión)
python prueba_registro.py   # hoja de registro (sin conexión)
python prueba_acis.py       # generación del Anexo III.b (sin conexión)
python prueba_programacion.py  # lector de programaciones (sin conexión)
python prueba_acis_ia.py    # volcado de la adaptación con IA (sin conexión)
python prueba_ia_api.py     # prueba REAL de la IA (usa la API y gasta saldo)
```

---

## Construir la distribución

```bash
pip install -r dev-requirements.txt
winget install JRSoftware.InnoSetup    # para el instalador (opcional)
.\construir.ps1
```

En `dist\` quedan: la carpeta `Adaptadocs\` (build `--onedir`), el instalador
`AdaptadocsSetup.exe`, la versión portable `Adaptadocs-portable.zip` y sus
archivos `.sha256`.

> Se usa **`--onedir`, no `--onefile`**, a propósito: los ejecutables «todo en
> uno» de PyInstaller se autoextraen al arrancar y Windows Defender los marca
> como falso positivo (`Trojan:Win32/Wacatac.B!ml`). La carpeta + instalador no.

En cada etiqueta `vX.Y.Z` que se sube al repositorio, GitHub Actions construye
todo y lo publica en la Release
(ver [`.github/workflows/release.yml`](.github/workflows/release.yml)).

---

## Limitaciones conocidas

- No lee el formato antiguo `.doc`; ábrelo en Word y guárdalo como `.docx`.
- El texto dentro de **cuadros de texto y formas** no se modifica (limitación de
  la librería `python-docx`).
- Fuentes como **OpenDyslexic** o **Lexend** deben estar instaladas en el equipo
  donde se abra el documento; si no, Word mostrará una fuente sustituta.
- La conversión de viñetas a lista numerada depende de que el documento use los
  estilos de lista estándar de Word.
- La adaptación con IA trabaja sobre los párrafos de primer nivel; el texto
  dentro de tablas no se reescribe (sí se le aplica el formato).
- La IA puede cometer errores: **revisa siempre** el documento adaptado antes de
  usarlo con el alumnado.

---

## Estructura

```
adaptadocs/
├── app.py              Ventana de escritorio (Tkinter): Formato / IA / ACIS
├── cli.py              Uso por línea de comandos y por lotes
├── crear_ejemplo.py    Genera un .docx de prueba
├── crear_acis.py       Genera un Anexo III.b (ACIS) desde un JSON
├── construir.ps1       Construye carpeta + instalador + zip portable
├── instalador.iss      Script del instalador (Inno Setup)
├── core/
│   ├── transformador.py  Formato (python-docx, sin conexión)
│   ├── perfiles.py       Perfiles de formato predefinidos
│   ├── ia.py             Llamada a la API de Anthropic (adaptación de contenido)
│   ├── aplicar_ia.py     Vuelca el resultado de la IA en el documento
│   ├── claves.py         Guardado seguro de la clave de API (keyring)
│   ├── registro.py       Hoja interna «qué se ha adaptado y por qué»
│   ├── registro.json     Textos y marco legal de esa hoja (editable)
│   ├── acis.py           Genera el Anexo III.b (ACIS) de ESO
│   ├── acis.json         Textos fijos y perfil de accesibilidad (editable)
│   ├── acis_ia.py        Adaptación de la programación al nivel de otro curso (IA)
│   ├── programacion.py   Lee competencias/criterios/contenidos de una programación
│   └── pipeline.py       Orquesta IA + formato
├── recursos/           Icono y datos de versión del .exe
└── .github/workflows/  CI y publicación automática
```

## Licencia

[MIT](LICENSE). Uso libre, también en centros educativos. Se agradece
mencionar el origen.
