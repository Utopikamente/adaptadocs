"""Uso por línea de comandos y por lotes.

Ejemplos:
    python cli.py entrada.docx
    python cli.py entrada.docx -o salida.docx --perfil Dislexia
    python cli.py carpeta_con_docx --perfil TDAH --resaltar "importante, recuerda, ojo"

Con adaptación de contenido por IA (necesita la variable ANTHROPIC_API_KEY):
    python cli.py entrada.docx --ia simplificar,glosario,preguntas --nivel "3º-4º de Primaria"
"""

from __future__ import annotations

import argparse
import os
import sys

from core.ia import MODELOS, NIVELES, NIVEL_POR_DEFECTO, OpcionesIA
from core.perfiles import PERFILES, PERFIL_POR_DEFECTO, opciones_de_perfil

_TAREAS_IA = ("simplificar", "glosario", "resumen", "preguntas", "pasos")


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
    from core.pipeline import adaptar_documento_completo
    from core.transformador import adaptar_documento

    parser = argparse.ArgumentParser(description="Adapta documentos de Word para el alumnado.")
    parser.add_argument("origen", help="Archivo .docx o carpeta con varios .docx")
    parser.add_argument("-o", "--salida", help="Archivo de salida (solo si 'origen' es un archivo)")
    parser.add_argument("--perfil", default=PERFIL_POR_DEFECTO, choices=list(PERFILES),
                        help="Perfil de adaptación de formato")
    parser.add_argument("--resaltar", default="", help="Palabras a resaltar separadas por comas")
    parser.add_argument("--color", default="AMARILLO",
                        choices=["AMARILLO", "VERDE", "TURQUESA", "ROSA", "GRIS"])
    parser.add_argument("--separar-pasos", default="no", choices=["no", "marcados", "auto"],
                        help="Separar procedimientos en pasos numerados (sin IA): "
                        "'marcados' = solo párrafos que empiezan por «PASOS:»; 'auto' = heurística")
    parser.add_argument("--pictogramas", action="store_true",
                        help="Añadir al final un banco de pictogramas de ARASAAC para las "
                        "palabras de --resaltar (necesita conexión)")
    parser.add_argument("--numerar-preguntas", action="store_true",
                        help="Renumerar de forma consecutiva los párrafos que sean preguntas "
                        "(terminan en «?»)")
    parser.add_argument("--espacio-respuestas", type=int, default=0,
                        help="Líneas en blanco a insertar tras cada pregunta detectada "
                        "para que el alumnado responda (0 = ninguna)")
    parser.add_argument(
        "--ia", default="",
        help="Tareas de IA separadas por comas: " + ", ".join(_TAREAS_IA)
        + " (necesita ANTHROPIC_API_KEY)",
    )
    parser.add_argument("--nivel", default=NIVEL_POR_DEFECTO, choices=list(NIVELES),
                        help="Nivel de lectura objetivo para la IA")
    parser.add_argument("--modelo-ia", default="claude-opus-5",
                        choices=sorted(set(MODELOS.values())),
                        help="Modelo de Claude para la adaptación de contenido")
    parser.add_argument("--preguntas", type=int, default=5,
                        help="Número de preguntas de comprensión si se pide 'preguntas'")
    args = parser.parse_args(argv)

    opciones = opciones_de_perfil(args.perfil)
    opciones.separar_en_pasos = args.separar_pasos
    if args.pictogramas:
        opciones.pictogramas = "resaltadas"
    opciones.numerar_preguntas = args.numerar_preguntas
    opciones.espacio_respuestas = args.espacio_respuestas
    if args.resaltar:
        opciones.resaltar_palabras = [p.strip() for p in args.resaltar.split(",") if p.strip()]
        opciones.color_resaltado = args.color

    tareas = {t.strip().lower() for t in args.ia.split(",") if t.strip()}
    desconocidas = tareas - set(_TAREAS_IA)
    if desconocidas:
        print(f"Tareas de IA no válidas: {', '.join(sorted(desconocidas))}", file=sys.stderr)
        return 2
    opciones_ia = None
    if tareas:
        opciones_ia = OpcionesIA(
            simplificar="simplificar" in tareas,
            glosario="glosario" in tareas,
            resumen="resumen" in tareas,
            preguntas="preguntas" in tareas,
            pasos="pasos" in tareas,
            nivel=args.nivel,
            modelo=args.modelo_ia,
            n_preguntas=args.preguntas,
        )
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Falta la variable de entorno ANTHROPIC_API_KEY.", file=sys.stderr)
            return 2

    entradas = _archivos(args.origen)
    if not entradas:
        print("No se han encontrado archivos .docx.", file=sys.stderr)
        return 1

    errores = 0
    for entrada in entradas:
        salida = args.salida if (args.salida and len(entradas) == 1) else _ruta_salida(entrada)
        try:
            if opciones_ia is not None:
                res = adaptar_documento_completo(
                    entrada, salida, opciones, opciones_ia, registrar=print
                )
                ia = res["ia"]
                print(
                    f"  IA: {ia.get('simplificados', 0)} reescritos · "
                    f"{ia.get('glosario', 0)} términos · {ia.get('preguntas', 0)} preguntas"
                )
                print(f"  Formato: {res['formato']['parrafos']} párrafos\n")
            else:
                resumen = adaptar_documento(entrada, salida, opciones, registrar=print)
                print(
                    f"  {resumen['parrafos']} párrafos · {resumen['resaltados']} resaltados · "
                    f"{resumen['procedimientos_en_pasos']} en pasos · "
                    f"{resumen['pictogramas']} pictogramas · "
                    f"{resumen['preguntas_numeradas']} preguntas numeradas · "
                    f"{resumen['preguntas_con_espacio']} con espacio para responder\n"
                )
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR con «{entrada}»: {exc}\n", file=sys.stderr)
            errores += 1

    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
