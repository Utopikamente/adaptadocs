"""Prueba REAL de la adaptación con IA (hace una llamada a la API y gasta saldo).

Requiere la variable de entorno ANTHROPIC_API_KEY (o una clave guardada en la app).

    python prueba_ia_api.py

Crea 'ejemplo.docx', lo adapta con simplificación + glosario + resumen +
preguntas y guarda 'ejemplo (IA).docx' para que lo abras en Word.
"""

from __future__ import annotations

import os
import sys

import crear_ejemplo
from core.claves import leer_clave
from core.ia import OpcionesIA
from core.perfiles import opciones_de_perfil
from core.pipeline import adaptar_documento_completo


def main() -> int:
    clave = os.environ.get("ANTHROPIC_API_KEY") or leer_clave()
    if not clave:
        print("Define ANTHROPIC_API_KEY o guarda la clave en la app.", file=sys.stderr)
        return 2

    if not os.path.exists("ejemplo.docx"):
        crear_ejemplo.main()

    opciones_ia = OpcionesIA(
        simplificar=True,
        glosario=True,
        resumen=True,
        preguntas=True,
        pasos=True,
        nivel="3º-4º de Primaria",
        modelo="claude-opus-5",
        n_preguntas=4,
    )

    res = adaptar_documento_completo(
        "ejemplo.docx",
        "ejemplo (IA).docx",
        opciones_de_perfil("Dislexia"),
        opciones_ia,
        api_key=clave,
        registrar=print,
    )

    ia = res["ia"]
    print("\nResumen IA:", {k: v for k, v in ia.items() if k != "_uso"})
    print("Tokens:", ia.get("_uso"))
    print("Guardado: ejemplo (IA).docx")
    return 0


if __name__ == "__main__":
    sys.exit(main())
