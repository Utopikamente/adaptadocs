"""Prueba REAL de la adaptación curricular con IA (llama a la API y gasta saldo).

    python prueba_acis_ia_api.py  "ruta/PROGRAMACION.docx"  "2.º ESO"  [barreras]

Lee la programación, pide a la IA los criterios, contenidos e instrumentos
adaptados al nivel indicado y genera «ACIS (borrador).docx».
Requiere ANTHROPIC_API_KEY (o una clave guardada en la app).
"""

from __future__ import annotations

import os
import sys

from core.acis import DatosACIS, MateriaACIS, generar_acis
from core.acis_ia import (
    OpcionesAdaptacionCurricular,
    adaptar_programacion,
    resultado_a_materia,
)
from core.claves import leer_clave
from core.programacion import leer_programacion


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print(__doc__)
        return 2

    ruta_prog, nivel = argv[0], argv[1]
    barreras = argv[2] if len(argv) > 2 else ""

    clave = os.environ.get("ANTHROPIC_API_KEY") or leer_clave()
    if not clave:
        print("Define ANTHROPIC_API_KEY o guarda la clave en la app.", file=sys.stderr)
        return 2

    prog = leer_programacion(ruta_prog)
    print(f"Programación: {len(prog.competencias)} competencias, "
          f"{len(prog.saberes_basicos)} bloques de saberes, "
          f"{len(prog.instrumentos)} instrumentos.")

    resultado = adaptar_programacion(
        prog,
        OpcionesAdaptacionCurricular(nivel_objetivo=nivel, barreras=barreras),
        api_key=clave,
        registrar=print,
    )
    print("\nAvisos de la IA:")
    for a in resultado.get("avisos", []):
        print("  -", a)

    materia = resultado_a_materia(
        prog, resultado,
        MateriaACIS(materia=prog.materia or "Materia", acs_determinada=True),
    )
    ruta, _ = generar_acis("ACIS (borrador).docx", DatosACIS(materias=[materia]))
    print(f"\nGuardado: {ruta}")
    print("Tokens:", resultado.get("_uso"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
