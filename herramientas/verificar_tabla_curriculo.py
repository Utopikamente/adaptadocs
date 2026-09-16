"""Automatiza la parte mecánica de la verificación "treinta filas al azar"
del plan de octubre: para una muestra de filas de `tabla_curriculo_eso.json`,
busca su texto en el .txt del que salieron (la extracción con PyMuPDF del PDF
del BOCM) y enseña las líneas originales alrededor, para no tener que
buscarlas a mano.

Importante — qué comprueba esto y qué NO:
- SÍ comprueba que `construir_tabla_curriculo.py` no ha introducido ningún
  error al reordenar el texto en filas (recorte, mezcla de criterios,
  atribución equivocada a una competencia, etc.): si una fila no aparece tal
  cual en el .txt de origen, hay un bug en el reordenado.
- NO comprueba que el propio PDF/.txt refleje bien la letra del BOCM (eso
  necesita tu ojo, comparando con el decreto publicado) ni que el decreto no
  haya sido modificado después por otra norma (p. ej. el Decreto 59/2024
  modifica el 65/2022 en algunos puntos; conviene comprobar aparte si el PDF
  de partida ya incorpora esos cambios o es el texto original de 2022).

Uso:

    python herramientas/verificar_tabla_curriculo.py tabla_curriculo_eso.json normativa12.txt --n=30

Escribe el informe en <tabla>_verificacion.txt (junto a la tabla) y también
lo resume por pantalla.
"""

from __future__ import annotations

import bisect
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from actualizar_curriculo_eso import cargar_lineas  # noqa: E402


def nt(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def indice_normalizado(lineas: list[str]) -> tuple[str, list[tuple[int, str]]]:
    """Índice para buscar texto sin que los saltos de línea del PDF estorben.

    Devuelve (texto_normalizado, no_vacias): `no_vacias` es la lista de
    (índice de línea original, línea normalizada) de las líneas con
    contenido, en orden; `texto_normalizado` es su concatenación separada
    por un espacio, en ese mismo orden."""
    no_vacias = [(i, nt(l)) for i, l in enumerate(lineas) if nt(l)]
    texto = " ".join(t for _, t in no_vacias)
    return texto, no_vacias


def localizar(texto_normalizado: str, no_vacias: list[tuple[int, str]], query: str):
    """Busca `query` (ya normalizado) en `texto_normalizado`. Si aparece,
    devuelve (línea original de inicio, línea original de fin); si no, None."""
    if not query:
        return None
    pos = texto_normalizado.find(query)
    if pos == -1:
        return None
    fin = pos + len(query)
    offsets: list[int] = []
    acumulado = 0
    for _, t in no_vacias:
        offsets.append(acumulado)
        acumulado += len(t) + 1
    k_ini = max(bisect.bisect_right(offsets, pos) - 1, 0)
    k_fin = max(bisect.bisect_right(offsets, fin - 1) - 1, k_ini)
    return no_vacias[k_ini][0], no_vacias[k_fin][0]


def _filas_a_verificar(tabla: dict) -> list[dict]:
    """Cada fila con una etiqueta y el texto que hay que localizar."""
    filas = []
    for f in tabla.get("criterios", []):
        filas.append({
            "etiqueta": f"[CRITERIO] {f['materia']} {f['curso']} {f['criterio_id']}",
            "texto": f["criterio_texto"],
        })
    for f in tabla.get("saberes", []):
        filas.append({
            "etiqueta": f"[SABER] {f['materia']} {f['curso']} {f['bloque_id']}",
            "texto": f["item"].lstrip("· ").strip(),
        })
    return filas


def verificar(tabla: dict, lineas_fuente: list[str], n: int, semilla: int | None = None) -> tuple[list[str], int, int]:
    """Devuelve (informe_por_filas, encontradas, no_encontradas)."""
    texto_norm, no_vacias = indice_normalizado(lineas_fuente)
    filas = _filas_a_verificar(tabla)
    if semilla is not None:
        random.seed(semilla)
    muestra = random.sample(filas, min(n, len(filas)))

    informe: list[str] = []
    encontradas = no_encontradas = 0
    for fila in muestra:
        query = nt(fila["texto"])
        resultado = localizar(texto_norm, no_vacias, query)
        informe.append(fila["etiqueta"])
        informe.append(f"  Texto en la tabla: {fila['texto'][:200]}")
        if resultado is None:
            no_encontradas += 1
            informe.append("  NO ENCONTRADO literalmente en el .txt de origen — revisar el reordenado.")
        else:
            encontradas += 1
            ini, fin = resultado
            desde = max(ini - 1, 0)
            hasta = min(fin + 1, len(lineas_fuente) - 1)
            informe.append(f"  Encontrado en las líneas {ini}-{fin} del .txt de origen:")
            for i in range(desde, hasta + 1):
                marca = ">>" if ini <= i <= fin else "  "
                informe.append(f"  {marca} {i}: {lineas_fuente[i].rstrip()}")
        informe.append("")
    return informe, encontradas, no_encontradas


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    n = 30
    for arg in sys.argv[3:]:
        if arg.startswith("--n="):
            n = int(arg.split("=", 1)[1])

    tabla = json.load(open(sys.argv[1], encoding="utf-8"))
    lineas_fuente = cargar_lineas(sys.argv[2])

    informe, encontradas, no_encontradas = verificar(tabla, lineas_fuente, n)

    ruta_salida = sys.argv[1].rsplit(".", 1)[0] + "_verificacion.txt"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write("\n".join(informe))

    print(f"Verificadas {encontradas + no_encontradas} filas: {encontradas} encontradas literalmente, "
          f"{no_encontradas} NO encontradas.")
    print(f"Informe completo en {ruta_salida}.")
    if no_encontradas:
        print("Hay filas que no se han encontrado tal cual — revísalas, puede haber un bug en el reordenado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
