"""Extrae el ANEXO II del Decreto 65/2022 (currículo de la ESO de la Comunidad
de Madrid) a un JSON con el texto oficial troceado por materia.

    python herramientas/extraer_curriculo_eso.py  "Decreto 65 2022.txt"  core/curriculo_eso.json

El .txt se obtiene con:  pdftotext -layout -enc UTF-8 "normativa (12).pdf" salida.txt
"""

from __future__ import annotations

import json
import re
import sys

MATERIAS = [
    "BIOLOGÍA Y GEOLOGÍA",
    "CIENCIAS DE LA COMPUTACIÓN",
    "CULTURA CLÁSICA",
    "DIGITALIZACIÓN",
    "ECONOMÍA Y EMPRENDIMIENTO",
    "EDUCACIÓN FÍSICA",
    "EDUCACIÓN PLÁSTICA, VISUAL Y AUDIOVISUAL",
    "EDUCACIÓN EN VALORES CÍVICOS Y ÉTICOS",
    "EXPRESIÓN ARTÍSTICA",
    "FILOSOFÍA",
    "FÍSICA Y QUÍMICA",
    "FORMACIÓN Y ORIENTACIÓN PERSONAL Y PROFESIONAL",
    "GEOGRAFÍA E HISTORIA",
    "LATÍN",
    "LENGUA CASTELLANA Y LITERATURA",
    "LENGUA EXTRANJERA",
    "MATEMÁTICAS",
    "MÚSICA",
    "SEGUNDA LENGUA EXTRANJERA",
    "TECNOLOGÍA Y DIGITALIZACIÓN",
    "TECNOLOGÍA",
]

_RUIDO = re.compile(
    r"^\s*(BOCM\b|BOLET[IÍ]N OFICIAL|P[áa]g\.\s|B\.O\.C\.M\.|VIERNES 22 DE JULIO|"
    r"BOCM-20220722|Núm\.\s*\d+)",
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
        else:
            vacias = 0
        salida.append(l.rstrip())
    return salida


def extraer(ruta_txt: str) -> dict:
    lineas = _limpiar(open(ruta_txt, encoding="utf-8").read().splitlines())
    # localizar el inicio del ANEXO II y del ANEXO III
    ini_anexo = next((i for i, l in enumerate(lineas) if l.strip() == "ANEXO II"), 0)
    fin_anexo = next((i for i, l in enumerate(lineas) if l.strip().startswith("ANEXO III")), len(lineas))
    cuerpo = lineas[ini_anexo:fin_anexo]

    marcas = [(l.strip(), i) for i, l in enumerate(cuerpo) if l.strip() in MATERIAS]
    resultado = {
        "fuente": "Decreto 65/2022, de 20 de julio — ANEXO II (Currículo de materias de la ESO). "
                  "Texto oficial (BOCM núm. 174, 22/07/2022).",
        "nota": "Cada entrada es el texto del anexo para esa materia (competencias específicas, "
                "criterios de evaluación y contenidos). Referencia para la adaptación curricular; editable.",
        "materias": {},
    }
    for k, (materia, ini) in enumerate(marcas):
        fin = marcas[k + 1][1] if k + 1 < len(marcas) else len(cuerpo)
        texto = re.sub(r"\n{2,}", "\n", "\n".join(cuerpo[ini + 1:fin]).strip())
        resultado["materias"][materia] = texto
    return resultado


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2
    datos = extraer(argv[0])
    with open(argv[1], "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    for materia, texto in datos["materias"].items():
        print(f"{materia}: {len(texto)} car.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
