"""Comprobación (sin red) del volcado de la ACIS generada con IA.

Verifica que `core.acis_ia.resultado_a_materia` convierte una respuesta
simulada de la IA en TODOS los campos de una `MateriaACIS` (competencias
reformuladas, criterios, contenidos, metodología, instrumentos + criterios de
calificación, y unidades), y que el documento resultante los recoge. La
llamada real a la API se prueba a mano con `prueba_acis_ia_api.py`.

    python prueba_acis_ia.py
"""

from __future__ import annotations

import os
import sys
import tempfile

from docx import Document

from core.acis import DatosACIS, MateriaACIS, generar_acis
from core.acis_ia import (
    OpcionesAdaptacionCurricular,
    _mensaje_usuario,
    categorias_necesidades,
    expandir_categoria,
    resultado_a_materia,
)
from core.programacion import Competencia, Programacion


def main() -> int:
    fallos: list[str] = []

    prog = Programacion(
        materia="Lengua Extranjera (Inglés)", curso="4.º ESO",
        competencias=[
            Competencia("1", "Comprender e interpretar textos orales y escritos.",
                        ["CCL2"], [("1.1.", "Extraer el sentido global de textos claros.")]),
            Competencia("2", "Producir textos escritos con organización clara.",
                        ["CCL1"], [("2.1.", "Redactar textos de extensión media coherentes.")]),
        ],
        saberes_basicos={"A. Comunicación": ["Funciones: describir, narrar."]},
        instrumentos=[("Writing", "Rúbrica")],
        unidades=[("UNIT 1 FAMILY MATTERS", "1ª evaluación")],
    )

    resultado = {
        "competencias": [
            {"numero": "1",
             "texto_reformulado": "Entender de qué trata un texto muy corto y sencillo, con apoyo visual.",
             "criterios_adaptados": [
                 {"referencia": "1.1.", "nivel": "Tercer ciclo de Primaria",
                  "texto": "Identificar de qué trata un texto corto y con dibujos."}]},
            {"numero": "2",
             "texto_reformulado": "Escribir frases cortas y ordenadas sobre un tema conocido.",
             "criterios_adaptados": [
                 {"referencia": "2.1.", "nivel": "Tercer ciclo de Primaria",
                  "texto": "Escribir 3-4 frases con una plantilla."}]},
        ],
        "contenidos": [
            {"bloque": "A. Comunicación", "nivel": "Tercer ciclo de Primaria",
             "items": ["Describir personas con frases simples.", "Contar la rutina diaria."]},
        ],
        "metodologia": "Apoyo de PT 2 h/semana; modelos resueltos; mucha repetición.",
        "instrumentos": [
            {"elemento": "Writing", "propuesta": "Plantilla de frases y banco de palabras con imágenes.",
             "justificacion": "Permite producir texto sin bloquearse."},
        ],
        "criterios_calificacion": "Writing 25 % · Listening 25 % · Speaking 25 % · Trabajo 25 %. "
                                  "No se penaliza la ortografía.",
        "unidades": [
            {"titulo": "UNIT 1 FAMILY MATTERS", "periodo": "1ª evaluación",
             "adaptacion": "La familia: miembros y describir a una persona con have got."},
        ],
        "avisos": ["El nivel de Primaria debe contrastarse con el Anexo II del Decreto 61/2022."],
    }

    base = MateriaACIS(materia="Lengua Extranjera (Inglés)", profesor="—",
                       departamento="Inglés", acs_determinada=True)
    materia = resultado_a_materia(prog, resultado, base)

    comprobaciones = {
        "competencias reformuladas": "1. Entender de qué trata" in materia.competencias,
        "criterios por competencia": "Competencia específica 1" in materia.criterios_evaluacion,
        "referencia y nivel del criterio": "1.1. (Tercer ciclo de Primaria)" in materia.criterios_evaluacion,
        "contenidos por bloque y nivel": "A. Comunicación (Tercer ciclo de Primaria)" in materia.contenidos,
        "ítems de contenido": "− Describir personas" in materia.contenidos,
        "metodología": "Apoyo de PT" in materia.metodologia,
        "instrumento adaptado": "Writing: Plantilla de frases" in materia.instrumentos,
        "criterios de calificación": "CRITERIOS DE CALIFICACIÓN" in materia.instrumentos
                                     and "No se penaliza la ortografía" in materia.instrumentos,
        "unidad adaptada": "UNIT 1 FAMILY MATTERS: La familia" in materia.unidades,
        "secuenciación con periodo": materia.secuenciacion == [("UNIT 1 FAMILY MATTERS", "1ª evaluación")],
        "casilla acs_determinada intacta": materia.acs_determinada is True,
    }
    for que, ok in comprobaciones.items():
        if not ok:
            fallos.append(f"resultado_a_materia: falla «{que}»")

    # El documento final recoge lo adaptado y no queda como pendiente.
    trabajo = tempfile.mkdtemp(prefix="adaptadocs-acisia-")
    ruta = os.path.join(trabajo, "ACIS.docx")
    generar_acis(ruta, DatosACIS(materias=[materia]))
    texto = "\n".join(c.text for fila in Document(ruta).tables[1].rows for c in fila.cells)
    if "[PENDIENTE" in texto:
        fallos.append("los campos adaptados no deberían salir como pendientes")
    for frag in ("Identificar de qué trata un texto", "Contar la rutina diaria",
                 "UNIT 1 FAMILY MATTERS", "No se penaliza la ortografía"):
        if frag not in texto:
            fallos.append(f"«{frag}» no llega al documento")

    # --- Perfil de accesibilidad: categoría -> necesidades funcionales --- #
    cats = categorias_necesidades()
    tea = next((c for c in cats if "TEA" in c), None)
    if tea:
        necesidades = expandir_categoria(tea)
        msg = _mensaje_usuario(
            prog,
            OpcionesAdaptacionCurricular(nivel_objetivo="Tercer ciclo de Primaria",
                                         necesidades=necesidades,
                                         referencia_curriculo="TEXTO OFICIAL DE EJEMPLO"),
        )
        if "PERFIL DE ACCESIBILIDAD" not in msg or necesidades[0] not in msg:
            fallos.append("el mensaje a la IA no incluye el perfil de accesibilidad")
        if tea in msg or "TEA" in msg:
            fallos.append("la etiqueta de categoría clínica no debe aparecer en el mensaje a la IA")
        if "SIGUE MATRICULADO" not in msg or "CURRÍCULO OFICIAL DE REFERENCIA" not in msg:
            fallos.append("el mensaje a la IA no deja claro el curso ni incluye el currículo oficial")
        if "UNIT 1 FAMILY MATTERS" not in msg:
            fallos.append("el mensaje a la IA no incluye las unidades de la programación")

    # Respuesta vacía: los campos quedan vacíos.
    vacia = resultado_a_materia(prog, {}, MateriaACIS(materia="X", acs_determinada=True))
    if vacia.criterios_evaluacion or vacia.contenidos or vacia.instrumentos or vacia.competencias:
        fallos.append("una respuesta vacía no debería rellenar campos")

    if fallos:
        print("PRUEBA ACIS-IA (sin red) FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1

    print("PRUEBA ACIS-IA (sin red) OK — competencias reformuladas, criterios, contenidos, "
          "metodología, instrumentos+calificación y unidades.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
