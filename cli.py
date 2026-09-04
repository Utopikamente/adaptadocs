"""Uso por línea de comandos y por lotes.

Ejemplos:
    python cli.py entrada.docx
    python cli.py entrada.docx -o salida.docx --perfil Dislexia
    python cli.py carpeta_con_docx --perfil TDAH --resaltar "importante, recuerda, ojo"
"""

from __future__ import annotations

import argparse
import os
import sys

from core.perfiles import PERFILES, PERFIL_POR_DEFECTO, opciones_de_perfil


def _ruta_salida(entrada: str) -> str:
    carpeta, nombre = os.path.split(entrada)
    raiz, _ = os.path.splitext(nombre)
    return os.path.join(carpeta, f"{raiz} (adaptado).docx")


def _archivos(origen: str) -> list[str]:
    if os.path.isdir(origen):
        return [
            os.path.join(origen, n)
            for n in sorted(os.listdir(origen))
            if n.lower().endswith(".docx") and "(adaptado)" not in n.lower()
        ]
    return [origen]


def main(argv: list[str] | None = None) -> int:
    from core.transformador import adaptar_documento  # import diferido: mensajes de error más claros

    parser = argparse.ArgumentParser(description="Adapta documentos de Word para el alumnado.")
    parser.add_argument("origen", help="Archivo .docx o carpeta con varios .docx")
    parser.add_argument("-o", "--salida", help="Archivo de salida (solo si 'origen' es un archivo)")
    parser.add_argument("--perfil", default=PERFIL_POR_DEFECTO, choices=list(PERFILES),
                        help="Perfil de adaptación")
    parser.add_argument("--resaltar", default="", help="Palabras a resaltar separadas por comas")
    parser.add_argument("--color", default="AMARILLO",
                        choices=["AMARILLO", "VERDE", "TURQUESA", "ROSA", "GRIS"])
    args = parser.parse_args(argv)

    opciones = opciones_de_perfil(args.perfil)
    if args.resaltar:
        opciones.resaltar_palabras = [p.strip() for p in args.resaltar.split(",") if p.strip()]
        opciones.color_resaltado = args.color

    entradas = _archivos(args.origen)
    if not entradas:
        print("No se han encontrado archivos .docx.", file=sys.stderr)
        return 1

    errores = 0
    for entrada in entradas:
        salida = args.salida if (args.salida and len(entradas) == 1) else _ruta_salida(entrada)
        try:
            resumen = adaptar_documento(entrada, salida, opciones, registrar=print)
            print(f"  {resumen['parrafos']} párrafos · {resumen['resaltados']} resaltados\n")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR con «{entrada}»: {exc}\n", file=sys.stderr)
            errores += 1

    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
