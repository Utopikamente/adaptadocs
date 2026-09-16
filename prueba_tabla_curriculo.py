"""Comprobación (sin red, sin PDF) de `herramientas/construir_tabla_curriculo.py`:
verifica que reordena un currículo ya parseado en la tabla fila-por-fila
(criterios y saberes básicos) con su columna de referencia, sin perder ni
inventar ningún dato, y que respeta las anomalías ya documentadas por el
propio decreto (no las corrige en silencio).

    python prueba_tabla_curriculo.py
"""

from __future__ import annotations

import sys

from herramientas.construir_tabla_curriculo import _nombre_legible, _referencia, construir_tabla


def main() -> int:
    fallos: list[str] = []

    datos = {
        "LENGUA CASTELLANA Y LITERATURA": {
            "ce": [
                {"id": "CE1", "texto": "Comprender textos.", "cc": "CCL1"},
                {"id": "CE2", "texto": "Producir textos.", "cc": "CCL2"},
            ],
            "cursos": {
                "1": {
                    "criterios": [
                        {"ce": "CE1", "id": "1.1", "texto": "Reconocer el tema de un texto."},
                        {"ce": "CE1", "id": "1.2", "texto": "Identificar la intención del emisor."},
                    ],
                    "saberes": [
                        {"b": "A", "t": "Comunicación", "items": ["El texto y sus tipos."]},
                    ],
                },
            },
            "anomalias": [],
            "intro": "...",
        },
        "MATEMÁTICAS": {
            "ce": [{"id": "CE1", "texto": "Resolver problemas.", "cc": "STEM1"}],
            "cursos": {
                "2": {
                    "criterios": [{"ce": "CE1", "id": "2.1", "texto": "Interpretar enunciados."}],
                    "saberes": [{"b": "A", "t": "Sentido numérico", "items": ["Los números racionales."]}],
                },
            },
            "anomalias": ['curso 2: el criterio impreso como "2.3" figura bajo "Competencia específica 3"'],
            "intro": "...",
        },
        "MÚSICA": {  # no está en la lista de materias pedida: no debe aparecer en la tabla
            "ce": [{"id": "CE1", "texto": "Escuchar.", "cc": "CCEC1"}],
            "cursos": {"1": {"criterios": [{"ce": "CE1", "id": "1.1", "texto": "Escuchar con atención."}],
                             "saberes": []}},
            "anomalias": [], "intro": "...",
        },
        # Matemáticas A/B (4.º ESO) no llevan marcador de curso propio en el
        # decreto -son de un único curso- así que el parser las etiqueta como
        # "curso único" ("0"), no como "4". Además, a veces queda una entrada
        # "4" residual pero VACÍA (sin criterios ni saberes): no debe ganarle
        # a la de "0", que es la que tiene contenido de verdad.
        "MATEMÁTICAS A": {
            "ce": [], "anomalias": [], "intro": "",
            "cursos": {
                "4": {"criterios": [], "saberes": []},
                "0": {"criterios": [{"ce": "CE1", "id": "1.1", "texto": "Resolver un problema aplicado."}],
                      "saberes": [{"b": "A", "t": "Aplicaciones", "items": ["Interés simple y compuesto."]}]},
            },
        },
        "MATEMÁTICAS B": {
            "ce": [], "anomalias": [], "intro": "",
            "cursos": {
                "0": {"criterios": [{"ce": "CE1", "id": "1.1", "texto": "Demostrar una propiedad matemática."}],
                      "saberes": [{"b": "A", "t": "Demostraciones", "items": ["Métodos de demostración."]}]},
            },
        },
    }

    tabla = construir_tabla(datos, ["LENGUA CASTELLANA Y LITERATURA", "MATEMÁTICAS"])

    if len(tabla["criterios"]) != 5:
        fallos.append(f"criterios = {len(tabla['criterios'])} (esperados 5: 2 Lengua + 1 Matemáticas + 1 Mat.A + 1 Mat.B)")
    if len(tabla["saberes"]) != 4:
        fallos.append(f"saberes = {len(tabla['saberes'])} (esperados 4: 1 Lengua + 1 Matemáticas + 1 Mat.A + 1 Mat.B)")
    if any(f["materia"] == "MÚSICA" for f in tabla["criterios"] + tabla["saberes"]):
        fallos.append("Música no se pidió y no debería aparecer en la tabla")

    fila = next((f for f in tabla["criterios"] if f["criterio_id"] == "1.2"), None)
    if fila is None:
        fallos.append("no se encuentra el criterio 1.2")
    else:
        if fila["competencia_texto"] != "Comprender textos.":
            fallos.append("el criterio no lleva el texto de SU competencia específica (CE1)")
        if fila["curso"] != "1.º ESO":
            fallos.append(f"curso mal formateado: «{fila['curso']}» (esperado «1.º ESO»)")
        if "Lengua Castellana y Literatura" not in fila["referencia"] or "Decreto 65/2022" not in fila["referencia"]:
            fallos.append(f"referencia incompleta: «{fila['referencia']}»")

    if tabla["anomalias"].get("MATEMÁTICAS") != datos["MATEMÁTICAS"]["anomalias"]:
        fallos.append("las anomalías del decreto no se han trasladado a la tabla")
    if "LENGUA CASTELLANA Y LITERATURA" in tabla["anomalias"]:
        fallos.append("Lengua no tenía anomalías y no debería aparecer en el diccionario")

    # El nombre de la materia se capitaliza para la referencia, sin mayúscula en los conectores.
    if _nombre_legible("LENGUA CASTELLANA Y LITERATURA") != "Lengua Castellana y Literatura":
        fallos.append(f"_nombre_legible mal capitalizado: «{_nombre_legible('LENGUA CASTELLANA Y LITERATURA')}»")
    if "y Literatura" not in _referencia("LENGUA CASTELLANA Y LITERATURA", "1"):
        fallos.append("la referencia no respeta la minúscula del conector «y»")
    # La "A"/"B" de las variantes es un identificador, no la preposición "a".
    if _nombre_legible("MATEMÁTICAS A") != "Matemáticas A":
        fallos.append(f"_nombre_legible confunde la variante «A» con la preposición: «{_nombre_legible('MATEMÁTICAS A')}»")

    # Matemáticas A/B (4.º ESO): deben aparecer con sus propias filas, curso
    # "4.º ESO" (no "curso único"), y heredando el texto de la competencia de
    # "MATEMÁTICAS" (el decreto no la repite). La entrada "4" vacía de A no
    # debe ganarle a la de "0", que es la que tiene contenido real.
    fila_a = next((f for f in tabla["criterios"] if f["materia"] == "MATEMÁTICAS A"), None)
    fila_b = next((f for f in tabla["criterios"] if f["materia"] == "MATEMÁTICAS B"), None)
    if fila_a is None or fila_b is None:
        fallos.append("Matemáticas A y/o B no aparecen en la tabla (4.º ESO se quedaría sin filas)")
    else:
        for nombre, fila in (("A", fila_a), ("B", fila_b)):
            if fila["curso"] != "4.º ESO":
                fallos.append(f"Matemáticas {nombre}: curso «{fila['curso']}» (esperado «4.º ESO»)")
            if fila["competencia_texto"] != "Resolver problemas.":
                fallos.append(f"Matemáticas {nombre}: no hereda el texto de la competencia de MATEMÁTICAS")
            if "Matemáticas " + nombre not in fila["referencia"]:
                fallos.append(f"Matemáticas {nombre}: la referencia no dice «Matemáticas {nombre}»: «{fila['referencia']}»")
    saberes_a = [f for f in tabla["saberes"] if f["materia"] == "MATEMÁTICAS A"]
    if not saberes_a:
        fallos.append("los saberes básicos de Matemáticas A no llegan a la tabla")

    if fallos:
        print("PRUEBA TABLA CURRÍCULO FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1

    print("PRUEBA TABLA CURRÍCULO OK — filas de criterios y saberes básicos, referencia, "
          "filtro de materias y anomalías trasladadas sin corregirlas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
