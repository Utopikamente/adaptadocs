"""Extrae el ANEXO II del Decreto 61/2022 (currículo de Educación Primaria de
la Comunidad de Madrid) a un JSON con el texto oficial troceado por área y
ciclo. La adaptación con IA usa ese texto como referencia; no hace falta
atomizarlo en objetos.

    python herramientas/extraer_curriculo_primaria.py  "Anexo II 612022.txt"  core/curriculo_primaria.json

El .txt se obtiene con:  pdftotext -layout -enc UTF-8 "Anexo II 612022.pdf" salida.txt
"""

from __future__ import annotations

import json
import re
import sys

AREAS = [
    "Ciencias de la Naturaleza",
    "Ciencias Sociales",
    "Educación Artística",
    "Educación Física",
    "Lengua Castellana y Literatura",
    "Lengua Extranjera: Inglés",
    "Matemáticas",
]
CICLOS = {"PRIMER CICLO": "Primer ciclo", "SEGUNDO CICLO": "Segundo ciclo",
          "TERCER CICLO": "Tercer ciclo"}

_RUIDO = re.compile(
    r"^\s*(BOCM\b|BOLET[IÍ]N OFICIAL|P[áa]g\.\s|B\.O\.C\.M\.|LUNES 18 DE JULIO|"
    r"BOCM-20220718|Núm\.\s*169)",
    re.IGNORECASE,
)


def _limpiar(lineas: list[str]) -> list[str]:
    salida, vacias = [], 0
    for l in lineas:
        if _RUIDO.match(l):
            continue
        if not l.strip():
            vacias += 1
            if vacias > 1:
                continue
            salida.append("")
        else:
            vacias = 0
            salida.append(l.rstrip())
    return salida


def _marcas_area(lineas: list[str]) -> list[tuple[str, int]]:
    return [(l.strip(), i) for i, l in enumerate(lineas) if l.strip() in AREAS]


def _marcas_ciclo(cuerpo: list[str]) -> list[tuple[str, int]]:
    """Primera aparición de cada ciclo en el cuerpo del área, en orden."""
    primero: dict[str, int] = {}
    for i, l in enumerate(cuerpo):
        u = l.strip().upper()
        for clave, nombre in CICLOS.items():
            if re.search(r"\b" + clave.replace(" ", r"\s+") + r"\b", u) and nombre not in primero:
                primero[nombre] = i
    return sorted(primero.items(), key=lambda x: x[1])


def extraer(ruta_txt: str) -> dict:
    lineas = _limpiar(open(ruta_txt, encoding="utf-8").read().splitlines())
    marcas = _marcas_area(lineas)
    resultado = {
        "fuente": "Decreto 61/2022, de 13 de julio — ANEXO II (Áreas de Educación "
                  "Primaria). Texto oficial (BOCM núm. 169, 18/07/2022).",
        "nota": "Cada entrada es el texto tal cual del anexo (competencias específicas, "
                "criterios de evaluación y contenidos del ciclo). Se usa como referencia "
                "para la adaptación curricular; editable.",
        "areas": {},
    }
    for k, (area, ini) in enumerate(marcas):
        fin = marcas[k + 1][1] if k + 1 < len(marcas) else len(lineas)
        cuerpo = lineas[ini + 1:fin]
        ciclos = _marcas_ciclo(cuerpo)
        intro = "\n".join(cuerpo[:ciclos[0][1]]).strip() if ciclos else "\n".join(cuerpo).strip()
        area_dict = {"introduccion": re.sub(r"\n{2,}", "\n", intro), "ciclos": {}}
        for c, (ciclo, j) in enumerate(ciclos):
            j_fin = ciclos[c + 1][1] if c + 1 < len(ciclos) else len(cuerpo)
            texto = "\n".join(cuerpo[j + 1:j_fin]).strip()
            texto = re.sub(r"\n{2,}", "\n", texto)
            area_dict["ciclos"][ciclo] = texto
        resultado["areas"][area] = area_dict
    return resultado


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    datos = extraer(argv[0])
    with open(argv[1], "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    for area, d in datos["areas"].items():
        ciclos = {c: len(t) for c, t in d["ciclos"].items()}
        print(f"{area}: intro {len(d['introduccion'])} car.; ciclos {ciclos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
