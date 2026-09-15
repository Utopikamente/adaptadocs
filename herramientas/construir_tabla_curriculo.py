"""Reordena el currículo oficial de la ESO (ya extraído y verificado por
`actualizar_curriculo_eso.py`) en una tabla fila por fila: una fila por
criterio de evaluación (con su competencia específica) y una fila por cada
saber básico, cada una con su columna de referencia al decreto.

Es el formato que necesita el emparejador (programación de aula <-> currículo
del nivel de referencia): la tabla de texto de `core/curriculo_eso.json` vale
para leerla, pero no para cruzarla fila a fila.

No vuelve a inventar nada: reutiliza el mismo parser ya verificado de
`actualizar_curriculo_eso.py` sobre el mismo .txt (extracción con PyMuPDF de
la capa de texto del PDF del BOCM, sin OCR). Uso:

    python herramientas/construir_tabla_curriculo.py normativa12.txt core/tabla_curriculo_eso.json

Por defecto solo procesa Lengua Castellana y Literatura y Matemáticas (el
80 % de las ACIS, según el plan de octubre-diciembre); pasa `--materias` con
nombres separados por "|" para ampliarlo.
"""

from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from actualizar_curriculo_eso import NOM_CURSO, _corregir_biologia, cargar_lineas, parsear  # noqa: E402

MATERIAS_POR_DEFECTO = ["LENGUA CASTELLANA Y LITERATURA", "MATEMÁTICAS"]

_CONECTORES = {"y", "e", "o", "de", "del", "la", "las", "los", "a", "en"}


def _nombre_legible(materia: str) -> str:
    """"LENGUA CASTELLANA Y LITERATURA" -> "Lengua Castellana y Literatura"
    (los conectores como "y"/"de" se dejan en minúscula, igual que hace el
    Taller de Programaciones con `bancoNombre()`)."""
    palabras = materia.lower().split()
    return " ".join(p if p in _CONECTORES else p.capitalize() for p in palabras)


def _referencia(materia: str, curso_key: str) -> str:
    curso = NOM_CURSO.get(curso_key, curso_key)
    return (f"Decreto 65/2022, de 20 de julio (BOCM 26/07/2022), Anexo II — "
            f"{_nombre_legible(materia)}, {curso}")


def construir_tabla(datos: dict, materias: list[str]) -> dict:
    """Devuelve {"criterios": [...], "saberes": [...], "anomalias": {...}}.

    Cada fila de `criterios` trae: materia, curso, competencia_id,
    competencia_texto, criterio_id, criterio_texto, referencia.
    Cada fila de `saberes` trae: materia, curso, bloque_id, bloque_titulo,
    item, referencia.
    """
    filas_criterios: list[dict] = []
    filas_saberes: list[dict] = []
    anomalias: dict[str, list[str]] = {}

    for materia in materias:
        M = datos.get(materia)
        if not M:
            continue
        if M.get("anomalias"):
            anomalias[materia] = M["anomalias"]

        textos_ce = {c["id"]: c["texto"] for c in M.get("ce", [])}
        for curso_key, curso in M.get("cursos", {}).items():
            ref = _referencia(materia, curso_key)
            for cr in curso.get("criterios", []):
                filas_criterios.append({
                    "materia": materia,
                    "curso": NOM_CURSO.get(curso_key, curso_key),
                    "competencia_id": cr["ce"],
                    "competencia_texto": textos_ce.get(cr["ce"], ""),
                    "criterio_id": cr["id"],
                    "criterio_texto": cr["texto"],
                    "referencia": ref,
                })
            for bloque in curso.get("saberes", []):
                for item in bloque.get("items", []):
                    filas_saberes.append({
                        "materia": materia,
                        "curso": NOM_CURSO.get(curso_key, curso_key),
                        "bloque_id": bloque["b"],
                        "bloque_titulo": bloque["t"],
                        "item": item,
                        "referencia": ref,
                    })

    return {"criterios": filas_criterios, "saberes": filas_saberes, "anomalias": anomalias}


def escribir_csv(filas: list[dict], ruta: str) -> None:
    if not filas:
        return
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    materias = MATERIAS_POR_DEFECTO
    for arg in sys.argv[3:]:
        if arg.startswith("--materias="):
            materias = arg.split("=", 1)[1].split("|")

    lineas = cargar_lineas(sys.argv[1])
    datos = parsear(lineas)
    _corregir_biologia(datos)
    tabla = construir_tabla(datos, materias)

    json.dump(tabla, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    base, _ = os.path.splitext(sys.argv[2])
    escribir_csv(tabla["criterios"], f"{base}_criterios.csv")
    escribir_csv(tabla["saberes"], f"{base}_saberes.csv")

    print(f"Escrito {sys.argv[2]} — {len(tabla['criterios'])} criterios, "
          f"{len(tabla['saberes'])} saberes básicos, materias: {', '.join(materias)}.")
    if tabla["anomalias"]:
        print("Anomalías del propio decreto (no corregidas, solo señaladas):")
        for materia, lista in tabla["anomalias"].items():
            for a in lista:
                print(f"  [{materia}] {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
