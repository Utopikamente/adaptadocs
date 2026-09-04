# Adaptadocs

[![Comprobaciones](https://github.com/Utopikamente/adaptadocs/actions/workflows/ci.yml/badge.svg)](https://github.com/Utopikamente/adaptadocs/actions/workflows/ci.yml)

Aplicación de escritorio para **transformar un documento `.docx` en otro `.docx`
adaptado**, pensada para crear materiales más accesibles para alumnado con
dificultades de aprendizaje (dislexia, TDAH, TEA, discapacidad intelectual leve,
baja visión…).

Tiene dos partes:

- **Formato y presentación** (siempre disponible, gratis, sin conexión): todo
  ocurre en tu ordenador. La única excepción es el **banco de pictogramas**: si lo
  activas, se piden a ARASAAC los dibujos de las palabras a ilustrar (solo esas
  palabras, no el documento).
- **Contenido con IA** (opcional): reescribe el texto a un nivel de lectura más
  sencillo, añade glosario, resumen y preguntas de comprensión. Necesita una
  clave de API de Anthropic y **envía el texto del documento a Claude** para
  procesarlo. Ver la sección [Adaptación de contenido con IA](#adaptación-de-contenido-con-ia-opcional).

---

## Descargar (Windows)

1. Descarga **[`Adaptadocs.exe`](https://github.com/Utopikamente/adaptadocs/releases/latest/download/Adaptadocs.exe)**
   (o entra en **[Releases](../../releases)** y coge el `.exe` de la última versión).
2. Haz doble clic. No necesita instalación ni permisos de administrador.

### El navegador y Windows avisan del archivo

El ejecutable **no está firmado digitalmente** (un certificado cuesta cientos de
euros al año), así que aparecerán dos avisos. Ambos son esperados:

- **Al descargar** (Chrome/Edge): «Adaptadocs.exe puede ser peligroso / no es
  habitual» → pulsa los tres puntos o la flecha → **Conservar** / **Conservar de
  todos modos**.
- **Al abrir** (SmartScreen, aviso azul): **Más información** → **Ejecutar de
  todas formas**.

Para comprobar que el archivo no se ha alterado, compara su huella con la del
archivo `Adaptadocs.exe.sha256` de la Release:

```powershell
Get-FileHash "Adaptadocs.exe" -Algorithm SHA256
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
- **Resalta** las palabras clave que indiques, con el color que elijas.
- Añade al final un **banco de pictogramas** ([ARASAAC](https://arasaac.org)) con
  las palabras que resaltes: apoyo visual para alumnado con TEL/TDL, TEA, etc.
  Necesita conexión. Los pictogramas tienen licencia **CC BY-NC-SA** (autor
  Sergio Palao; Gobierno de Aragón): la atribución se incluye en el documento
  y su uso comercial requiere permiso de ARASAAC.
- Respeta imágenes, tablas y la estructura de apartados del documento.
- Crea un archivo nuevo con el sufijo `(adaptado)`; **el original no se toca**.

Incluye **perfiles** predefinidos (General, Dislexia, TDAH, TEA, Discapacidad
intelectual leve, Baja visión, TEL/TDL con apoyo visual) que puedes retocar antes
de generar el documento.

---

## Adaptación de contenido con IA (opcional)

En la pestaña **«Contenido con IA»** de la ventana puedes pedir, además del
formato:

- **Simplificar el texto** a un nivel de lectura (de 1º de Primaria a 2º de ESO,
  o pautas de Lectura Fácil), conservando datos, cifras y nombres propios.
- **Convertir procedimientos en pasos numerados.**
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
```

Probar rápidamente:

```bash
python crear_ejemplo.py
python cli.py ejemplo.docx --perfil Dislexia --resaltar "glucosa, oxígeno"
python prueba.py          # comprobación de formato
python prueba_ia.py       # comprobación de la capa de IA (sin conexión)
python prueba_ia_api.py   # prueba REAL de la IA (usa la API y gasta saldo)
```

---

## Construir el ejecutable

```bash
pip install -r dev-requirements.txt
.\construir.ps1
```

El resultado queda en `dist\Adaptadocs.exe` junto a su archivo `.sha256`.

En cada etiqueta `vX.Y.Z` que se sube al repositorio, GitHub Actions construye el
ejecutable y lo publica automáticamente en la Release
(ver [`.github/workflows/release.yml`](.github/workflows/release.yml)).

Instalador opcional (asistente + acceso directo), con
[Inno Setup](https://jrsoftware.org/isinfo.php):

```bash
winget install JRSoftware.InnoSetup
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
```

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
├── app.py              Ventana de escritorio (Tkinter), 2 pestañas: Formato / IA
├── cli.py              Uso por línea de comandos y por lotes
├── crear_ejemplo.py    Genera un .docx de prueba
├── construir.ps1       Construye el .exe
├── instalador.iss      Script del instalador (Inno Setup)
├── core/
│   ├── transformador.py  Formato (python-docx, sin conexión)
│   ├── perfiles.py       Perfiles de formato predefinidos
│   ├── ia.py             Llamada a la API de Anthropic (adaptación de contenido)
│   ├── aplicar_ia.py     Vuelca el resultado de la IA en el documento
│   ├── pictogramas.py    Pictogramas de ARASAAC (banco de apoyo visual)
│   ├── claves.py         Guardado seguro de la clave de API (keyring)
│   └── pipeline.py       Orquesta IA + formato
├── recursos/           Icono y datos de versión del .exe
└── .github/workflows/  CI y publicación automática
```

## Licencia

[MIT](LICENSE). Uso libre, también en centros educativos. Se agradece
mencionar el origen.
