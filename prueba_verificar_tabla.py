"""Comprobación (sin red, sin PDF) de `herramientas/verificar_tabla_curriculo.py`:
que localiza el texto de una fila entre líneas partidas por saltos de página
o de columna, y que avisa (no inventa) cuando un texto no aparece.

    python prueba_verificar_tabla.py
"""

from __future__ import annotations

import sys

from herramientas.verificar_tabla_curriculo import indice_normalizado, localizar, verificar


def main() -> int:
    fallos: list[str] = []

    # Simula el .txt YA filtrado de furniture por `cargar_lineas` (esta función
    # trabaja después de ese filtro): un criterio partido en varias líneas por
    # el salto de página/columna del PDF, como pasa de verdad.
    lineas_fuente = [
        "Competencias específicas.",
        "1. Comprender textos.",
        "",
        "Criterios de evaluación.",
        "1.1 Reconocer el tema",
        "de un texto sencillo",
        "leído en clase.",
        "1.2 Identificar la intención",
        "del emisor.",
    ]
    texto_norm, no_vacias = indice_normalizado(lineas_fuente)

    encontrado = localizar(texto_norm, no_vacias, "Reconocer el tema de un texto sencillo leído en clase.")
    if encontrado is None:
        fallos.append("no localiza un texto partido en varias líneas por el salto de página/columna")
    elif encontrado != (4, 6):
        fallos.append(f"localiza el texto en las líneas equivocadas: {encontrado} (esperado (4, 6))")

    no_existe = localizar(texto_norm, no_vacias, "Esto no aparece en ningún sitio del documento.")
    if no_existe is not None:
        fallos.append("no debería 'encontrar' un texto que no está en el documento")

    vacio = localizar(texto_norm, no_vacias, "")
    if vacio is not None:
        fallos.append("una consulta vacía no debería devolver una coincidencia")

    # `verificar` sobre una tabla pequeña: una fila correcta y una inventada.
    tabla = {
        "criterios": [
            {"materia": "X", "curso": "1.º ESO", "criterio_id": "1.1",
             "criterio_texto": "Reconocer el tema de un texto sencillo leído en clase."},
            {"materia": "X", "curso": "1.º ESO", "criterio_id": "9.9",
             "criterio_texto": "Este criterio no existe en el documento de origen."},
        ],
        "saberes": [],
    }
    informe, encontradas, no_encontradas = verificar(tabla, lineas_fuente, n=2, semilla=1)
    if encontradas != 1 or no_encontradas != 1:
        fallos.append(f"verificar: encontradas={encontradas}, no_encontradas={no_encontradas} (esperado 1 y 1)")
    if not any("NO ENCONTRADO" in linea for linea in informe):
        fallos.append("el informe no señala la fila inventada como NO ENCONTRADO")

    if fallos:
        print("PRUEBA VERIFICAR TABLA FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1

    print("PRUEBA VERIFICAR TABLA OK — localiza texto partido entre líneas, "
          "detecta lo inexistente y genera el informe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
