"""Comprobación de las orientaciones deterministas de la ACIS (sin conexión).

    python prueba_acis_orientaciones.py

Verifica que `core.acis_orientaciones.orientaciones` compone, para cada
apartado, el texto fijo + la referencia del curso destino + (si el nivel es
Primaria y el área se reconoce) el currículo de Primaria + las recomendaciones
del perfil de accesibilidad.
"""

from __future__ import annotations

import sys

from core.acis_orientaciones import (
    cargar_curriculo_primaria,
    detectar_area_primaria,
    detectar_ciclo,
    es_nivel_primaria,
    orientaciones,
)
from core.acis import cargar_textos
from core.programacion import Competencia, Programacion


def main() -> int:
    fallos: list[str] = []
    textos = cargar_textos()

    # --- Detección de área y ciclo -------------------------------- #
    if detectar_area_primaria("Lengua Extranjera (Inglés)", textos) != "Lengua Extranjera: Inglés":
        fallos.append("no detecta el área de Primaria para «Lengua Extranjera (Inglés)»")
    if detectar_area_primaria("Biología y Geología", textos) != "Ciencias de la Naturaleza":
        fallos.append("no detecta el área de Primaria para «Biología y Geología»")
    if detectar_ciclo("Tercer ciclo de Primaria (nivel de 6.º)") != "Tercer ciclo":
        fallos.append("no detecta «Tercer ciclo»")
    if detectar_ciclo("6.º de Primaria") != "Tercer ciclo":
        fallos.append("no detecta el ciclo a partir de «6.º»")
    if es_nivel_primaria("2.º ESO"):
        fallos.append("«2.º ESO» no debería considerarse nivel de Primaria")

    # --- Programaciones de ejemplo ------------------------------- #
    prog_materia = Programacion(
        materia="Lengua Extranjera (Inglés)", curso="4.º ESO",
        competencias=[
            Competencia("1", "Comprender e interpretar textos.", ["CCL2"], []),
            Competencia("2", "Producir textos escritos.", ["CCL1"], []),
        ],
    )
    prog_destino = Programacion(
        materia="Lengua Extranjera (Inglés)", curso="2.º ESO",
        competencias=[
            Competencia("1", "Comprender textos sencillos.", ["CCL2"],
                        [("1.1.", "Captar la información esencial de textos breves.")]),
        ],
        saberes_basicos={"A. Comunicación": ["Funciones: describir, narrar."]},
        instrumentos=[("Listening", "Prueba oral")],
    )
    necesidades = [
        "Necesita lenguaje literal y explícito: evitar ironía, metáforas, dobles sentidos y frases hechas.",
    ]
    # las necesidades se pasan por clave, no por texto: recuperamos las claves
    claves = ["lenguaje_literal", "mas_tiempo"]

    # --- ESO -> ESO (sin currículo de Primaria) ------------------ #
    o1 = orientaciones(prog_materia, prog_destino, nivel_objetivo="2.º ESO", necesidades=claves)
    for apartado in ("competencias", "criterios_evaluacion", "contenidos", "metodologia", "instrumentos"):
        if not o1.get(apartado):
            fallos.append(f"falta la orientación de «{apartado}»")
    if "Se mantienen las competencias" not in o1["competencias"] or "1. Comprender" not in o1["competencias"]:
        fallos.append("la orientación de competencias no lista las de la materia")
    if "información esencial de textos breves" not in o1["criterios_evaluacion"]:
        fallos.append("criterios: no incluye la referencia del curso destino")
    if "Prueba oral" not in o1["instrumentos"]:
        fallos.append("instrumentos: no incluye los del curso destino")
    if "ampliar el tiempo" not in o1["instrumentos"].lower():
        fallos.append("instrumentos: no incluye la recomendación de «más tiempo»")
    if "ejemplo resuelto" not in o1["metodologia"].lower():
        fallos.append("metodología: no incluye la recomendación de «lenguaje literal»")
    marca_primaria = "Currículo oficial de Educación Primaria (Decreto 61/2022, Anexo II)"
    if marca_primaria in o1["criterios_evaluacion"]:
        fallos.append("no debería volcar el currículo de Primaria si el nivel es ESO")

    # --- ESO -> Primaria (con currículo, si está el JSON) -------- #
    curr = cargar_curriculo_primaria()
    if curr.get("areas"):
        o2 = orientaciones(prog_materia, prog_destino,
                           nivel_objetivo="Tercer ciclo de Primaria", necesidades=claves)
        if marca_primaria not in o2["criterios_evaluacion"]:
            fallos.append("criterios: no vuelca el currículo de Primaria cuando el nivel es tercer ciclo")
        if "Lengua Extranjera: Inglés, Tercer ciclo" not in o2["criterios_evaluacion"]:
            fallos.append("criterios: no nombra el área y el ciclo de Primaria")
        if marca_primaria not in o2["contenidos"]:
            fallos.append("contenidos: no vuelca el currículo de Primaria")

    if fallos:
        print("PRUEBA ORIENTACIONES FALLIDA:")
        for f in fallos:
            print("  -", f)
        return 1
    print("PRUEBA ORIENTACIONES OK — texto fijo, referencia del destino, currículo de Primaria y recomendaciones del perfil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
