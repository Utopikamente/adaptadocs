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

`emparejar_programacion()` junta todo en una `MateriaACIS` lista para
`core.acis.generar_acis`: cada criterio/saber sale marcado como cita literal
o, si no hay equivalente, como pendiente de adaptar -nunca en blanco, nunca
inventado- con su aviso correspondiente en el panel amarillo del documento.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from .acis import MateriaACIS, redaccion_alternativa
from .programacion import Competencia, Programacion

_RUTA_TABLA = os.path.join(os.path.dirname(__file__), "tabla_curriculo_eso.json")

# Todavía no se genera aquí una propuesta adaptada con IA para los huecos
# (criterios o saberes sin equivalente literal): se deja explícito, nunca en
# blanco, a la espera de conectar ese paso (pensado sobre `core.acis_ia`).
_PENDIENTE_IA = ("[Sin equivalente literal en el nivel de referencia — pendiente de generar "
                 "una propuesta adaptada con IA, o redactarla a mano]")

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
    nivel de referencia si existe. Tres estados posibles: `encontrado` (cita
    literal del decreto), `adaptado` (sin equivalente literal, pero con una
    propuesta generada por IA a partir del criterio de origen -ver
    `core.emparejador_ia`-), o ninguno de los dos (pendiente, sin generar
    todavía)."""

    numero: str                 # tal como venía en la programación, p. ej. "1.1."
    competencia: str            # "CE1"
    texto_origen: str
    encontrado: bool
    adaptado: bool = False       # True si `texto_referencia` es una propuesta de IA, no cita literal
    texto_referencia: str = ""  # texto literal o adaptado del criterio de referencia
    referencia: str = ""        # cita al decreto, o nota de que es una propuesta adaptada


@dataclass
class SaberEmparejado:
    """Un bloque de saberes básicos de la programación de origen, con su
    equivalente en el nivel de referencia si existe (por título, no por
    letra). Mismos tres estados que `CriterioEmparejado`."""

    bloque_origen: str                             # clave tal como venía, p. ej. "A. Comunicación"
    titulo: str                                    # "Comunicación"
    items_origen: list[str] = field(default_factory=list)
    encontrado: bool = False
    adaptado: bool = False
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


# --------------------------------------------------------------------------- #
# Texto para el Anexo III.b (todavía sin IA: los huecos quedan pendientes)
# --------------------------------------------------------------------------- #

def texto_criterios(resultado: list[CriterioEmparejado]) -> str:
    """Texto para `MateriaACIS.criterios_evaluacion`: agrupado por
    competencia específica, cada criterio marcado como cita literal,
    adaptado por IA o pendiente -nunca en blanco-, y siempre con el hueco de
    redacción alternativa del profesor."""
    if not resultado:
        return ""
    bloques: dict[str, list[CriterioEmparejado]] = {}
    for r in resultado:
        bloques.setdefault(r.competencia, []).append(r)

    partes: list[str] = []
    for ce, items in bloques.items():
        lineas = [f"Competencia específica {ce}"]
        for r in items:
            if r.encontrado:
                lineas.append(f"  {r.numero} ({r.referencia} — CITA LITERAL)")
                lineas.append(f"      {r.texto_referencia}")
            elif r.adaptado:
                lineas.append(f"  {r.numero} ({r.referencia})")
                lineas.append(f"      {r.texto_referencia}")
            else:
                lineas.append(f"  {r.numero} (SIN EQUIVALENTE en el nivel de referencia)")
                lineas.append(f"      {_PENDIENTE_IA}")
            lineas.append(redaccion_alternativa())
        partes.append("\n".join(lineas))
    return "\n\n".join(partes)


def texto_saberes(resultado: list[SaberEmparejado]) -> str:
    """Texto para `MateriaACIS.contenidos`, con el mismo criterio que
    `texto_criterios`: cita literal, adaptado por IA o pendiente, y siempre
    con el hueco de redacción alternativa."""
    if not resultado:
        return ""
    partes: list[str] = []
    for r in resultado:
        if r.encontrado:
            etiqueta = "CITA LITERAL"
        elif r.adaptado:
            etiqueta = r.referencia
        else:
            etiqueta = "SIN EQUIVALENTE en el nivel de referencia"
        lineas = [f"{r.bloque_origen} ({etiqueta})"]
        if r.encontrado or r.adaptado:
            lineas += [f"  − {it}" for it in r.items_referencia]
        else:
            lineas.append(f"  {_PENDIENTE_IA}")
        lineas.append(redaccion_alternativa())
        partes.append("\n".join(lineas))
    return "\n\n".join(partes)


def avisos(criterios: list[CriterioEmparejado], saberes: list[SaberEmparejado]) -> list[str]:
    """Un aviso por cada criterio o saber adaptado por IA o todavía
    pendiente, para el panel amarillo del Anexo III.b (`MateriaACIS.avisos_ia`).
    Los literales (cita del decreto) no llevan aviso."""
    lista: list[str] = []
    for r in criterios:
        if r.encontrado:
            continue
        if r.adaptado:
            lista.append(
                f"El criterio {r.numero} (competencia {r.competencia}) no tiene equivalente literal en "
                "el nivel de referencia: se ha generado una propuesta adaptada. Revísala y edítala si no "
                "encaja con el nivel real del alumno."
            )
        else:
            lista.append(
                f"El criterio {r.numero} (competencia {r.competencia}) no tiene equivalente literal "
                "en el nivel de referencia: falta generar una propuesta adaptada, o redactarla a mano."
            )
    for r in saberes:
        if r.encontrado:
            continue
        if r.adaptado:
            lista.append(
                f"El bloque de saberes básicos «{r.titulo}» no tiene equivalente literal en el nivel de "
                "referencia: se ha generado una propuesta adaptada. Revísala y edítala si no encaja con "
                "el nivel real del alumno."
            )
        else:
            lista.append(
                f"El bloque de saberes básicos «{r.titulo}» no tiene equivalente literal en el nivel de "
                "referencia: falta generar una propuesta adaptada, o redactarla a mano."
            )
    return lista


def emparejar_programacion(
    materia: str,
    programacion: Programacion,
    curso_referencia: str,
    tabla: dict,
    base: MateriaACIS | None = None,
) -> MateriaACIS:
    """Compone una `MateriaACIS` a partir del emparejamiento determinista de
    `programacion` contra el nivel de referencia. Todavía sin IA: los
    criterios y saberes sin equivalente literal quedan marcados como
    pendientes de adaptar (nunca en blanco, nunca inventados), con su aviso
    correspondiente. `base` aporta materia, profesor, departamento y la
    casilla `acs_determinada` (que decide una persona)."""
    resultado_cr = emparejar_criterios(materia, programacion.competencias, curso_referencia, tabla)
    resultado_sa = emparejar_saberes(materia, programacion.saberes_basicos, curso_referencia, tabla)

    m = base or MateriaACIS(materia=materia)
    m.criterios_evaluacion = texto_criterios(resultado_cr)
    m.contenidos = texto_saberes(resultado_sa)
    m.avisos_ia = list(m.avisos_ia) + avisos(resultado_cr, resultado_sa)
    return m
