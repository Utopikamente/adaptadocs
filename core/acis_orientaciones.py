"""Orientaciones deterministas (sin IA) para cada apartado de la ACIS.

Para cada apartado del Anexo III.b (competencias, criterios de evaluación,
contenidos, metodología, e instrumentos/criterios de calificación) compone un
texto de ayuda a partir de:

- el texto fijo de `acis.json` (qué pide el anexo, cómo citar el curso/ciclo),
- lo que trae la programación del curso destino (ya está a ese nivel),
- si el nivel objetivo es de Educación Primaria y se reconoce el área, el
  texto oficial del currículo de Primaria (`curriculo_primaria.json`),
- las recomendaciones asociadas a las necesidades del perfil de accesibilidad.

No usa conexión. El resultado se muestra como ayuda; no entra en el .docx.
"""

from __future__ import annotations

import json
import os
import re

from .acis import cargar_textos, materia_desde_programacion

_RUTA_CURRICULO = os.path.join(os.path.dirname(__file__), "curriculo_primaria.json")

_CICLOS = {
    "primer ciclo": "Primer ciclo", "1er ciclo": "Primer ciclo", "1.º ciclo": "Primer ciclo",
    "segundo ciclo": "Segundo ciclo", "2.º ciclo": "Segundo ciclo",
    "tercer ciclo": "Tercer ciclo", "3er ciclo": "Tercer ciclo", "3.º ciclo": "Tercer ciclo",
}
_CURSO_A_CICLO = {
    "1.º": "Primer ciclo", "2.º": "Primer ciclo",
    "3.º": "Segundo ciclo", "4.º": "Segundo ciclo",
    "5.º": "Tercer ciclo", "6.º": "Tercer ciclo",
}


def cargar_curriculo_primaria() -> dict:
    try:
        with open(_RUTA_CURRICULO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"areas": {}}


def es_nivel_primaria(nivel_objetivo: str) -> bool:
    n = (nivel_objetivo or "").lower()
    return "primaria" in n or any(c in n for c in _CICLOS)


def detectar_ciclo(nivel_objetivo: str) -> str | None:
    n = (nivel_objetivo or "").lower()
    for clave, nombre in _CICLOS.items():
        if clave in n:
            return nombre
    for curso, ciclo in _CURSO_A_CICLO.items():
        if curso in n or curso.replace(".º", "º") in n:
            return ciclo
    return None


def detectar_area_primaria(nombre_materia: str, textos: dict) -> str | None:
    mapa = textos.get("orientaciones", {}).get("areas_primaria", {})
    bajo = (nombre_materia or "").lower()
    for palabra, area in mapa.items():
        if palabra in bajo:
            return area
    return None


def _texto_curriculo_primaria(nombre_materia, nivel_objetivo, textos, curriculo) -> str:
    if not es_nivel_primaria(nivel_objetivo):
        return ""
    area = detectar_area_primaria(nombre_materia, textos)
    ciclo = detectar_ciclo(nivel_objetivo)
    if not area or not ciclo:
        return ""
    trozo = curriculo.get("areas", {}).get(area, {}).get("ciclos", {}).get(ciclo, "")
    if not trozo:
        return ""
    cab = textos["orientaciones"]["encabezado_referencia_primaria"].format(area=area, ciclo=ciclo)
    return f"{cab}\n{trozo}"


def _recomendaciones(necesidades: list[str], campo: str, textos: dict) -> str:
    recs = textos.get("perfil_accesibilidad", {}).get("recomendaciones", {})
    lineas = []
    for clave in necesidades or []:
        entrada = recs.get(clave, {})
        if entrada.get(campo):
            lineas.append(f"- {entrada[campo]}")
    if not lineas:
        return ""
    return textos["orientaciones"]["encabezado_recomendaciones"] + "\n" + "\n".join(lineas)


def _juntar(*bloques: str) -> str:
    return "\n\n".join(b.strip() for b in bloques if b and b.strip())


def orientaciones(
    prog_materia,
    prog_destino,
    nivel_objetivo: str = "",
    necesidades: list[str] | None = None,
    curriculo=None,
) -> dict[str, str]:
    """Devuelve {apartado: texto de orientación}. `prog_materia` es la
    programación de la materia (para las competencias que se mantienen);
    `prog_destino` la del curso al que se adapta."""
    textos = cargar_textos()
    o = textos["orientaciones"]
    curriculo = curriculo if curriculo is not None else cargar_curriculo_primaria()
    necesidades = necesidades or []

    nombre = getattr(prog_materia, "materia", "") or getattr(prog_destino, "materia", "")
    ref_primaria = _texto_curriculo_primaria(nombre, nivel_objetivo, textos, curriculo)

    # Competencias (se mantienen las de la materia)
    comps = []
    for c in getattr(prog_materia, "competencias", []) or getattr(prog_destino, "competencias", []):
        comps.append(f"{c.numero}. {c.texto}")
    bloque_comps = ("Se mantienen las competencias específicas de la materia:\n" + "\n".join(comps)) if comps else ""

    # Referencia del curso destino
    destino = materia_desde_programacion(prog_destino) if prog_destino is not None else None
    ref_destino_cri = ref_destino_con = ref_destino_ins = ""
    if destino is not None:
        enc = o["encabezado_referencia_destino"]
        if destino.criterios_evaluacion:
            ref_destino_cri = f"{enc}\n{destino.criterios_evaluacion}"
        if destino.contenidos:
            ref_destino_con = f"{enc}\n{destino.contenidos}"
        if destino.instrumentos:
            ref_destino_ins = f"{enc}\n{destino.instrumentos}"

    return {
        "competencias": _juntar(o["competencias"], bloque_comps),
        "criterios_evaluacion": _juntar(o["criterios_evaluacion"], ref_destino_cri, ref_primaria),
        "contenidos": _juntar(o["contenidos"], ref_destino_con, ref_primaria),
        "metodologia": _juntar(o["metodologia"], _recomendaciones(necesidades, "metodologia", textos)),
        "instrumentos": _juntar(
            o["instrumentos"], ref_destino_ins, _recomendaciones(necesidades, "instrumentos", textos)
        ),
    }
