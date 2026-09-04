"""Comprobación rápida de que la adaptación hace lo esperado.

    python prueba.py

Genera un documento de ejemplo, lo adapta con varios perfiles y verifica el
resultado. Sale con código 0 si todo va bien, 1 si algo falla. Lo usa también
la integración continua.
"""

from __future__ import annotations

import os
import sys
import tempfile

from docx import Document

from core.perfiles import opciones_de_perfil
from core.transformador import adaptar_documento
import crear_ejemplo


def _aprox(valor: float, esperado: float, tol: float = 0.02) -> bool:
    return abs(valor - esperado) <= tol


def main() -> int:
    fallos: list[str] = []
    trabajo = tempfile.mkdtemp(prefix="adaptadocs-prueba-")
    origen = os.path.join(trabajo, "ejemplo.docx")

    cwd = os.getcwd()
    os.chdir(trabajo)
    try:
        crear_ejemplo.main()
    finally:
        os.chdir(cwd)

    # --- Perfil Dislexia --------------------------------------------- #
    salida = os.path.join(trabajo, "dislexia.docx")
    opciones = opciones_de_perfil("Dislexia")
    opciones.resaltar_palabras = ["glucosa", "oxígeno", "estomas"]
    resumen = adaptar_documento(origen, salida, opciones)

    doc = Document(salida)

    if not _aprox(doc.sections[0].left_margin.cm, 3.0):
        fallos.append(f"margen izquierdo = {doc.sections[0].left_margin.cm} cm (esperado ~3.0)")

    cuerpo = doc.paragraphs[1]
    run = cuerpo.runs[0]
    if run.font.name != "Verdana":
        fallos.append(f"fuente = {run.font.name!r} (esperado 'Verdana')")
    if run.font.size is None or not _aprox(run.font.size.pt, 14.0, 0.1):
        fallos.append(f"tamaño = {run.font.size} (esperado 14 pt)")
    if cuerpo.paragraph_format.line_spacing not in (1.5,):
        fallos.append(f"interlineado = {cuerpo.paragraph_format.line_spacing} (esperado 1.5)")

    from docx.enum.text import WD_ALIGN_PARAGRAPH

    if cuerpo.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
        fallos.append("el párrafo sigue justificado")

    if resumen["resaltados"] < 3:
        fallos.append(f"palabras resaltadas = {resumen['resaltados']} (esperado >= 3)")

    resaltadas = [
        r.text
        for p in doc.paragraphs
        for r in p.runs
        if r.font.highlight_color is not None
    ]
    if not any("glucosa" in t.lower() for t in resaltadas):
        fallos.append(f"no se resaltó 'glucosa'; resaltadas: {resaltadas}")

    # --- Perfil TDAH: viñetas -> lista numerada --------------------- #
    salida_tdah = os.path.join(trabajo, "tdah.docx")
    resumen_tdah = adaptar_documento(origen, salida_tdah, opciones_de_perfil("TDAH"))
    if resumen_tdah["vinetas_convertidas"] < 1:
        fallos.append("no se convirtió ninguna viñeta en lista numerada (perfil TDAH)")

    # --- El original no se toca ------------------------------------- #
    if _aprox(Document(origen).sections[0].left_margin.cm, 3.0):
        fallos.append("¡el documento original ha sido modificado!")

    if fallos:
        print("PRUEBA FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1

    print("PRUEBA OK — formato, resaltado, viñetas y no-modificación del original.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
