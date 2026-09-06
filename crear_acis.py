"""Genera un Anexo III.b (ACIS) de ESO a partir de un archivo JSON de datos.

    python crear_acis.py --ejemplo             # crea «ejemplo_acis.json»
    python crear_acis.py datos.json            # -> ACIS.docx
    python crear_acis.py datos.json salida.docx

El JSON tiene esta forma (los campos vacíos salen como pendientes en el
documento, y una materia sin «acs_determinada: true» no se incluye):

    {
      "localidad": "Madrid",
      "fecha": "15 de octubre de 2026",
      "profesor_de": "Biología y Geología",
      "departamento_vb": "Biología y Geología",
      "materias": [
        {
          "materia": "Biología y Geología",
          "profesor": "…", "departamento": "…",
          "acs_determinada": true,
          "competencias": "",
          "criterios_evaluacion": "…",
          "contenidos": "…",
          "metodologia": "…",
          "instrumentos": "…",
          "unidades": "…",
          "secuenciacion": [["UD 1. …", "1er trimestre"]]
        }
      ]
    }
"""

from __future__ import annotations

import json
import sys

from core.acis import datos_desde_dict, generar_acis

_EJEMPLO = {
    "localidad": "Madrid",
    "fecha": "15 de octubre de 2026",
    "profesor_de": "Biología y Geología",
    "departamento_vb": "Biología y Geología",
    "materias": [
        {
            "materia": "Biología y Geología",
            "profesor": "",
            "departamento": "Biología y Geología",
            "acs_determinada": True,
            "competencias": "",
            "criterios_evaluacion": "1.1. (2.º ESO) Identificar las características de los seres vivos.\n"
                                    "Área de Ciencias de la Naturaleza, 3.er ciclo de Primaria: 2.1. Reconocer "
                                    "la célula como unidad de vida.",
            "contenidos": "La célula: partes y funciones (2.º ESO).\n"
                          "3.er ciclo de Primaria: los seres vivos y su clasificación.",
            "metodologia": "Apoyo de PT 2 horas semanales; trabajo por tareas cortas con apoyo visual.",
            "instrumentos": "Pruebas orales y escritas adaptadas; rúbricas; no penalizar ortografía.",
            "unidades": "UD 1 a 6 de la programación, con adaptación de actividades.",
            "secuenciacion": [
                ["UD 1. La célula", "1er trimestre"],
                ["UD 2. La nutrición", "2.º trimestre"],
            ],
        }
    ],
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] == "--ejemplo":
        with open("ejemplo_acis.json", "w", encoding="utf-8") as f:
            json.dump(_EJEMPLO, f, ensure_ascii=False, indent=2)
        print("Creado ejemplo_acis.json")
        return 0

    if not argv:
        print(__doc__)
        return 2

    entrada = argv[0]
    salida = argv[1] if len(argv) > 1 else "ACIS.docx"

    with open(entrada, encoding="utf-8") as f:
        datos = datos_desde_dict(json.load(f))

    ruta, avisos = generar_acis(salida, datos)
    print(f"Creado {ruta}")
    for aviso in avisos:
        print("AVISO:", aviso)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
