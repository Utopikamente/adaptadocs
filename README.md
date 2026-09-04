# Adaptador de documentos Word

Aplicación de escritorio para **transformar un documento `.docx` en otro `.docx`
adaptado**, pensada para crear materiales más accesibles para alumnado con
dificultades de aprendizaje (dislexia, TDAH, TEA, discapacidad intelectual leve,
baja visión…).

Esta versión trabaja **solo sobre el formato y la presentación**. No cambia el
contenido del texto ni envía nada a internet: todo ocurre en tu ordenador.

---

## Descargar (Windows)

1. Ve a la página de **[Releases](../../releases)** y descarga
   `Adaptador Word.exe` de la última versión.
2. Haz doble clic. No necesita instalación ni permisos de administrador.

### "Windows protegió su PC"

El ejecutable **no está firmado digitalmente** (un certificado cuesta cientos de
euros al año), así que la primera vez Windows SmartScreen mostrará un aviso azul.
Es esperado:

1. Pulsa **Más información**.
2. Pulsa **Ejecutar de todas formas**.

Para comprobar que el archivo no se ha alterado, compara su huella con la del
archivo `Adaptador Word.exe.sha256` de la Release:

```powershell
Get-FileHash "Adaptador Word.exe" -Algorithm SHA256
```

---

## Qué hace

- Cambia la **tipografía** y el **tamaño** de letra en todo el documento.
- Ajusta el **interlineado** y el **espacio entre párrafos**.
- Convierte el texto **justificado** en alineado a la izquierda.
- Amplía los **márgenes** y fuerza **una sola columna**.
- Pone el texto en **negro** (alto contraste).
- Pone los **títulos en negrita**.
- Convierte las **viñetas en una lista numerada** (pasos), opcional.
- **Resalta** las palabras clave que indiques, con el color que elijas.
- Respeta imágenes, tablas y la estructura de apartados del documento.
- Crea un archivo nuevo con el sufijo `(adaptado)`; **el original no se toca**.

Incluye **perfiles** predefinidos (General, Dislexia, TDAH, TEA, Discapacidad
intelectual leve, Baja visión) que puedes retocar antes de generar el documento.

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
```

---

## Construir el ejecutable

```bash
pip install -r dev-requirements.txt
.\construir.ps1
```

El resultado queda en `dist\Adaptador Word.exe` junto a su archivo `.sha256`.

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

---

## Estructura

```
adaptador-docx/
├── app.py              Ventana de escritorio (Tkinter)
├── cli.py              Uso por línea de comandos y por lotes
├── crear_ejemplo.py    Genera un .docx de prueba
├── construir.ps1       Construye el .exe
├── instalador.iss      Script del instalador (Inno Setup)
├── core/
│   ├── transformador.py  Lógica de transformación (python-docx)
│   └── perfiles.py       Perfiles predefinidos
├── recursos/           Icono y datos de versión del .exe
└── .github/workflows/  CI y publicación automática
```

## Licencia

[MIT](LICENSE). Uso libre, también en centros educativos. Se agradece
mencionar el origen.
