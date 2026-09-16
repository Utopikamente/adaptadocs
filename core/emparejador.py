"""Emparejador determinista entre la programación real de un alumno y el
currículo oficial de un nivel de referencia inferior (`core/tabla_curriculo_eso.json`).

Regla acordada con el autor: dentro de una materia, las competencias
específicas son las mismas en toda la etapa de ESO (solo cambian los
criterios y su dificultad por curso), así que un criterio se empareja por
"misma competencia específica + mismo número de criterio" en el curso de
referencia. Si ese número exacto no existe en el nivel de referencia, aquí
NO se inventa nada: se marca como sin equivalente (`encontrado=False`).
Generar una propuesta adaptada para esos huecos es un paso aparte -pensado
para reutilizar `core.acis_ia`- que todavía no se conecta desde este módulo.

Los saberes básicos no tienen letra de bloque estable entre cursos (a
diferencia de las competencias, ver commit de "Matemáticas A/B"): se
emparejan por el TÍTULO del bloque, no por su letra.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from .programacion import Competencia

_RUTA_TABLA = os.path.join(os.path.dirname(__file__), "tabla_curriculo_eso.json")

_RE_TITULO_BLOQUE = re.compile(r"^[A-Z]\.\s+(.+)$")


def cargar_tabla_curriculo(ruta: str = _RUTA_TABLA) -> dict:
    """Lee `tabla_curriculo_eso.json` (o la ruta que se indique)."""
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _normalizar_ce(numero: str) -> str:
    """"1", "ce1" o "CE1" -> "CE1" (en la programación puede venir con o sin
    el prefijo "CE"; en la tabla siempre lleva el prefijo)."""
    n = (numero or "").strip()
    return n.upper() if n.upper().startswith("CE") else f"CE{n}"


def _normalizar_criterio_id(codigo: str) -> str:
    """"1.1." o " 1.1 " -> "1.1" (la tabla no lleva el punto final que sí
    añade `core.programacion._trocear_criterios`)."""
    return (codigo or "").strip().rstrip(".")


def _titulo_bloque(clave: str) -> str:
    """"A. Comunicación" -> "Comunicación"; si la clave no tiene el patrón
    "letra. título" (p. ej. viene de "(sin bloque)"), se deja tal cual."""
    m = _RE_TITULO_BLOQUE.match((clave or "").strip())
    return m.group(1).strip() if m else (clave or "").strip()


@dataclass
class CriterioEmparejado:
    """Un criterio de la programación de origen, con su equivalente en el
    nivel de referencia si existe."""

    numero: str                 # tal como venía en la programación, p. ej. "1.1."
    competencia: str            # "CE1"
    texto_origen: str
    encontrado: bool
    texto_referencia: str = ""  # texto literal del criterio de referencia (si se encontró)
    referencia: str = ""        # cita al decreto (si se encontró)


@dataclass
class SaberEmparejado:
    """Un bloque de saberes básicos de la programación de origen, con su
    equivalente en el nivel de referencia si existe (por título, no por letra)."""

    bloque_origen: str                             # clave tal como venía, p. ej. "A. Comunicación"
    titulo: str                                    # "Comunicación"
    items_origen: list[str] = field(default_factory=list)
    encontrado: bool = False
    items_referencia: list[str] = field(default_factory=list)
    referencia: str = ""


def _indice_criterios(tabla: dict, materia: str, curso: str) -> dict[str, dict]:
    """{criterio_id: fila de la tabla} para una materia y curso concretos."""
    return {
        f["criterio_id"]: f
        for f in tabla.get("criterios", [])
        if f["materia"].upper() == materia.upper() and f["curso"] == curso
    }


def _indice_saberes(tabla: dict, materia: str, curso: str) -> dict[str, dict]:
    """{título de bloque: {"items": [...], "referencia": ...}} para una
    materia y curso concretos, agrupando las filas de la tabla por bloque."""
    indice: dict[str, dict] = {}
    for f in tabla.get("saberes", []):
        if f["materia"].upper() != materia.upper() or f["curso"] != curso:
            continue
        entrada = indice.setdefault(f["bloque_titulo"], {"items": [], "referencia": f["referencia"]})
        entrada["items"].append(f["item"])
    return indice


def emparejar_criterios(
    materia: str,
    competencias: list[Competencia],
    curso_referencia: str,
    tabla: dict,
) -> list[CriterioEmparejado]:
    """Recorre todos los criterios de todas las competencias de la
    programación de origen y busca su equivalente literal en el nivel de
    referencia. Devuelve una fila por criterio, lo haya encontrado o no."""
    indice_ref = _indice_criterios(tabla, materia, curso_referencia)
    resultado: list[CriterioEmparejado] = []
    for comp in competencias:
        ce = _normalizar_ce(comp.numero)
        for codigo, texto in comp.criterios:
            cid = _normalizar_criterio_id(codigo)
            fila_ref = indice_ref.get(cid)
            if fila_ref is not None and fila_ref["competencia_id"] == ce:
                resultado.append(CriterioEmparejado(
                    numero=codigo, competencia=ce, texto_origen=texto, encontrado=True,
                    texto_referencia=fila_ref["criterio_texto"], referencia=fila_ref["referencia"],
                ))
            else:
                resultado.append(CriterioEmparejado(
                    numero=codigo, competencia=ce, texto_origen=texto, encontrado=False,
                ))
    return resultado


def emparejar_saberes(
    materia: str,
    saberes_basicos: dict[str, list[str]],
    curso_referencia: str,
    tabla: dict,
) -> list[SaberEmparejado]:
    """Igual que `emparejar_criterios`, pero para los bloques de saberes
    básicos de la programación de origen, emparejados por título de bloque."""
    indice_ref = _indice_saberes(tabla, materia, curso_referencia)
    resultado: list[SaberEmparejado] = []
    for clave, items in saberes_basicos.items():
        titulo = _titulo_bloque(clave)
        entrada = indice_ref.get(titulo)
        if entrada is not None:
            resultado.append(SaberEmparejado(
                bloque_origen=clave, titulo=titulo, items_origen=list(items), encontrado=True,
                items_referencia=list(entrada["items"]), referencia=entrada["referencia"],
            ))
        else:
            resultado.append(SaberEmparejado(
                bloque_origen=clave, titulo=titulo, items_origen=list(items), encontrado=False,
            ))
    return resultado
