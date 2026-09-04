"""Comprobación de la capa de IA que NO usa la red.

Verifica que `core.aplicar_ia.aplicar_resultado` vuelca correctamente sobre el
documento una respuesta simulada (párrafos reescritos, pasos, glosario, resumen
y preguntas). La llamada real a la API se prueba a mano con `prueba_ia_api.py`.

    python prueba_ia.py
"""

from __future__ import annotations

import sys
import tempfile

from docx import Document

from core.aplicar_ia import aplicar_resultado
from core.pipeline import _extraer_bloques
import crear_ejemplo


def main() -> int:
    fallos: list[str] = []

    trabajo = tempfile.mkdtemp(prefix="adaptador-ia-")
    import os

    cwd = os.getcwd()
    os.chdir(trabajo)
    try:
        crear_ejemplo.main()
    finally:
        os.chdir(cwd)

    doc = Document(f"{trabajo}/ejemplo.docx")
    bloques, por_id = _extraer_bloques(doc)

    # Localiza ids reales del documento de ejemplo
    id_parrafo_intro = next(b.id for b in bloques if b.tipo == "parrafo")
    id_titulo = next(b.id for b in bloques if b.tipo == "titulo")

    datos = {
        "parrafos_simplificados": [
            {"id": id_parrafo_intro, "texto": "Las plantas fabrican su comida. Usan el sol."}
        ],
        "parrafos_en_pasos": [],
        "glosario": [
            {"termino": "glucosa", "definicion": "El alimento que fabrica la planta."},
            {"termino": "oxígeno", "definicion": "Un gas que necesitamos para respirar."},
        ],
        "resumen": [
            {"apartado": "La fotosíntesis", "puntos": ["Las plantas hacen su comida.", "Sueltan oxígeno."]}
        ],
        "preguntas": [
            "¿Qué usan las plantas para fabricar su alimento?",
            "¿Qué gas liberan las plantas?",
        ],
    }

    resumen = aplicar_resultado(doc, datos, por_id)

    salida = f"{trabajo}/ejemplo-ia.docx"
    doc.save(salida)
    releido = Document(salida)
    textos = [p.text for p in releido.paragraphs]

    if resumen["simplificados"] != 1:
        fallos.append(f"simplificados = {resumen['simplificados']} (esperado 1)")
    if not any("fabrican su comida" in t for t in textos):
        fallos.append("no se ve el párrafo reescrito en el documento")
    if resumen["glosario"] != 2 or "Glosario" not in textos:
        fallos.append("falta la sección Glosario")
    if "Preguntas de comprensión" not in textos:
        fallos.append("falta la sección de preguntas")
    if resumen["preguntas"] != 2:
        fallos.append(f"preguntas = {resumen['preguntas']} (esperado 2)")
    if "Resumen" not in textos:
        fallos.append("falta la sección Resumen")
    # el resumen debe ir cerca del principio, no al final
    if "Resumen" in textos and textos.index("Resumen") > textos.index("Glosario"):
        fallos.append("el resumen no está al principio")

    # Prueba de 'pasos': un párrafo se convierte en varias entradas de lista
    doc2 = Document(f"{trabajo}/ejemplo.docx")
    bloques2, por_id2 = _extraer_bloques(doc2)
    id_algun_parrafo = next(b.id for b in bloques2 if b.tipo == "parrafo")
    n_parrafos_antes = len(doc2.paragraphs)
    r2 = aplicar_resultado(
        doc2,
        {
            "parrafos_simplificados": [],
            "parrafos_en_pasos": [
                {"id": id_algun_parrafo, "pasos": ["Paso uno.", "Paso dos.", "Paso tres."]}
            ],
            "glosario": [],
            "resumen": [],
            "preguntas": [],
        },
        por_id2,
    )
    if r2["en_pasos"] != 1:
        fallos.append(f"en_pasos = {r2['en_pasos']} (esperado 1)")
    if len(doc2.paragraphs) != n_parrafos_antes + 2:
        fallos.append(
            f"pasos: {len(doc2.paragraphs)} párrafos (esperado {n_parrafos_antes + 2})"
        )

    if fallos:
        print("PRUEBA IA (sin red) FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1

    print("PRUEBA IA (sin red) OK — reescritura, pasos, glosario, resumen y preguntas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
