# Historial de cambios

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
