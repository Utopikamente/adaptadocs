"""Comprobación (sin red) del volcado de la adaptación curricular con IA.

Verifica que `core.acis_ia.resultado_a_materia` convierte una respuesta
simulada de la IA en los campos de una `MateriaACIS`, y que el documento
resultante recoge los criterios, contenidos e instrumentos adaptados. La
llamada real a la API se prueba a mano con `prueba_acis_ia_api.py`.

    python prueba_acis_ia.py
"""

from __future__ import annotations

import os
import sys
import tempfile

from docx import Document

from core.acis import MateriaACIS, generar_acis, DatosACIS
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
        materia="Inglés (Avanzado)", curso="4.º ESO",
        competencias=[
            Competencia("1", "Comprender e interpretar textos orales y escritos.",
                        ["CCL2", "CP1"], [("1.1.", "Extraer el sentido global de textos claros.")]),
            Competencia("2", "Producir textos escritos con organización clara.",
                        ["CCL1"], [("2.1.", "Redactar textos de extensión media coherentes.")]),
        ],
        saberes_basicos={"A. Comunicación": ["Funciones: describir, narrar."]},
        instrumentos=[("Writing", "Rúbrica")],
    )

    resultado = {
        "competencias": [
            {"numero": "1", "criterios_adaptados": [
                {"referencia": "1.1.", "nivel": "2.º ESO",
                 "texto": "Identificar de qué trata un texto corto y sencillo."}]},
            {"numero": "2", "criterios_adaptados": [
                {"referencia": "2.1.", "nivel": "6.º de Primaria (tercer ciclo)",
                 "texto": "Escribir frases cortas y ordenadas sobre un tema conocido."}]},
        ],
        "contenidos": [
            {"bloque": "A. Comunicación", "nivel": "2.º ESO",
             "items": ["Describir personas y lugares con frases simples.",
                       "Narrar hechos en pasado con conectores básicos."]},
        ],
        "instrumentos": [
            {"elemento": "Writing", "propuesta": "Rúbrica de 3 niveles con ejemplos y más tiempo.",
             "justificacion": "Reduce la carga de lectura y da un modelo claro."},
        ],
        "avisos": ["El criterio 2.1. se ha bajado a Primaria: revisar con orientación."],
    }

    base = MateriaACIS(materia="Inglés (Avanzado)", profesor="—",
                       departamento="Inglés", acs_determinada=True,
                       competencias="No se adapta ninguna competencia específica.",
                       metodologia="Apoyo de AL 2 h/semana.", unidades="UD 1 a 6 con adaptación.",
                       secuenciacion=[("UD 1", "1er trimestre")])
    materia = resultado_a_materia(prog, resultado, base)

    if "Competencia específica 1" not in materia.criterios_evaluacion:
        fallos.append("los criterios no se agrupan por competencia")
    if "1.1. (2.º ESO)" not in materia.criterios_evaluacion:
        fallos.append("no se ve la referencia y el nivel del criterio 1.1.")
    if "Primaria" not in materia.criterios_evaluacion:
        fallos.append("no se ve el nivel de Primaria en el criterio 2.1.")
    if "A. Comunicación (2.º ESO)" not in materia.contenidos:
        fallos.append("los contenidos no llevan bloque y nivel")
    if "− Describir personas" not in materia.contenidos:
        fallos.append("no se ven los ítems de contenido adaptados")
    if "Writing:" not in materia.instrumentos or "más tiempo" in materia.instrumentos.lower() and \
            "Rúbrica de 3 niveles" not in materia.instrumentos:
        fallos.append("no se ve la propuesta de instrumento adaptada")
    if materia.acs_determinada is not True:
        fallos.append("resultado_a_materia no debe tocar la casilla acs_determinada de la base")

    # El documento final recoge lo adaptado y no queda como pendiente.
    trabajo = tempfile.mkdtemp(prefix="adaptadocs-acisia-")
    ruta = os.path.join(trabajo, "ACIS.docx")
    generar_acis(ruta, DatosACIS(materias=[materia]))
    tabla = Document(ruta).tables[1]
    texto = "\n".join(c.text for fila in tabla.rows for c in fila.cells)
    if "[PENDIENTE" in texto:
        fallos.append("los campos adaptados no deberían salir como pendientes")
    if "Identificar de qué trata un texto" not in texto:
        fallos.append("el criterio adaptado no llega al documento")
    if "Narrar hechos en pasado" not in texto:
        fallos.append("el contenido adaptado no llega al documento")

    # --- Perfil de accesibilidad: categoría -> necesidades funcionales --- #
    cats = categorias_necesidades()
    if not cats:
        fallos.append("no hay categorías de perfil de accesibilidad en acis.json")
    tea = next((c for c in cats if "TEA" in c), None)
    if tea:
        necesidades = expandir_categoria(tea)
        if not necesidades or any(len(n) < 10 for n in necesidades):
            fallos.append(f"expandir_categoria({tea!r}) devolvió algo raro: {necesidades}")
        # El mensaje a la IA incluye las necesidades funcionales y NO la etiqueta.
        msg = _mensaje_usuario(
            prog,
            OpcionesAdaptacionCurricular(nivel_objetivo="2.º ESO", necesidades=necesidades),
            None,
        )
        if "PERFIL DE ACCESIBILIDAD" not in msg:
            fallos.append("el mensaje a la IA no incluye el perfil de accesibilidad")
        if necesidades[0] not in msg:
            fallos.append("las necesidades funcionales no llegan al mensaje de la IA")
        if tea in msg or "TEA" in msg:
            fallos.append("la etiqueta de categoría clínica no debe aparecer en el mensaje a la IA")

    # Respuesta vacía: los campos quedan vacíos (y saldrían como pendientes).
    vacia = resultado_a_materia(prog, {"competencias": [], "contenidos": [], "instrumentos": []},
                                MateriaACIS(materia="X", acs_determinada=True))
    if vacia.criterios_evaluacion or vacia.contenidos or vacia.instrumentos:
        fallos.append("una respuesta vacía no debería rellenar campos")

    if fallos:
        print("PRUEBA ACIS-IA (sin red) FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1

    print("PRUEBA ACIS-IA (sin red) OK — criterios por competencia, contenidos por bloque, "
          "instrumentos y volcado al documento.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
