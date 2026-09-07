"""Orientaciones deterministas (sin IA) para cada apartado de la ACIS.

Para cada apartado del Anexo III.b (competencias, criterios de evaluación,
contenidos, metodología, e instrumentos/criterios de calificación) compone un
texto de ayuda a partir de:

- el texto fijo de `acis.json` (qué pide el anexo, cómo citar el curso/ciclo),
- el **currículo oficial** de la materia: ESO (Decreto 65/2022) y, si el nivel
  objetivo es de Primaria y se reconoce el área, Primaria (Decreto 61/2022),
- lo que traiga la programación del curso destino (si se ha podido leer),
- las recomendaciones asociadas a las necesidades del perfil de accesibilidad.

Funciona con cero, una o dos programaciones. No usa conexión. El resultado se
muestra como ayuda; no entra en el .docx.
"""

from __future__ import annotations

import json
import os

from .acis import cargar_textos, materia_desde_programacion

_DIR = os.path.dirname(__file__)
_RUTA_PRIMARIA = os.path.join(_DIR, "curriculo_primaria.json")
_RUTA_ESO = os.path.join(_DIR, "curriculo_eso.json")

_CICLOS = {
    "primer ciclo": "Primer ciclo", "1er ciclo": "Primer ciclo", "1.º ciclo": "Primer ciclo",
    "segundo ciclo": "Segundo ciclo", "2.º ciclo": "Segundo ciclo",
    "tercer ciclo": "Tercer ciclo", "3er ciclo": "Tercer ciclo", "3.º ciclo": "Tercer ciclo",
}
_CURSO_A_CICLO = {"1.º": "Primer ciclo", "2.º": "Primer ciclo", "3.º": "Segundo ciclo",
                  "4.º": "Segundo ciclo", "5.º": "Tercer ciclo", "6.º": "Tercer ciclo"}

_LIMITE = 7000  # caracteres máximos de un trozo de currículo en el panel


def _cargar(ruta: str, clave: str) -> dict:
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {clave: {}}


def cargar_curriculo_primaria() -> dict:
    return _cargar(_RUTA_PRIMARIA, "areas")


def cargar_curriculo_eso() -> dict:
    return _cargar(_RUTA_ESO, "materias")


def _recortar(texto: str, fuente: str) -> str:
    if len(texto) <= _LIMITE:
        return texto
    return texto[:_LIMITE].rstrip() + f"\n[…] Texto completo en {fuente}."


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


def detectar_materia_eso(nombre_materia: str, curriculo_eso: dict) -> str | None:
    bajo = (nombre_materia or "").lower()
    if not bajo:
        return None
    materias = list(curriculo_eso.get("materias", {}))
    # coincidencia por palabras clave de la clave oficial
    for clave in materias:
        palabras = [p for p in clave.lower().replace(",", " ").split() if len(p) > 3
                    and p not in ("y", "de", "la", "en")]
        if palabras and any(p in bajo for p in palabras):
            return clave
    return None


def _texto_eso(nombre, curriculo_eso, textos) -> str:
    clave = detectar_materia_eso(nombre, curriculo_eso)
    if not clave:
        return ""
    trozo = curriculo_eso.get("materias", {}).get(clave, "")
    if not trozo:
        return ""
    cab = textos["orientaciones"].get(
        "encabezado_referencia_eso",
        "Currículo oficial de ESO (Decreto 65/2022, Anexo II) — {materia}:",
    ).format(materia=clave)
    return f"{cab}\n{_recortar(trozo, 'core/curriculo_eso.json')}"


def _texto_primaria(nombre, nivel_objetivo, textos, curriculo) -> str:
    if not es_nivel_primaria(nivel_objetivo):
        return ""
    area = detectar_area_primaria(nombre, textos)
    ciclo = detectar_ciclo(nivel_objetivo)
    if not area or not ciclo:
        return ""
    trozo = curriculo.get("areas", {}).get(area, {}).get("ciclos", {}).get(ciclo, "")
    if not trozo:
        return ""
    cab = textos["orientaciones"]["encabezado_referencia_primaria"].format(area=area, ciclo=ciclo)
    return f"{cab}\n{_recortar(trozo, 'core/curriculo_primaria.json')}"


def texto_referencia(nombre_materia: str, nivel_objetivo: str) -> str:
    """Texto del currículo oficial para pasar a la IA: el de la materia en ESO
    y, si el nivel baja a Primaria y se reconoce el área, el de Primaria."""
    textos = cargar_textos()
    trozos = [
        _texto_eso(nombre_materia, cargar_curriculo_eso(), textos),
        _texto_primaria(nombre_materia, nivel_objetivo, textos, cargar_curriculo_primaria()),
    ]
    return "\n\n".join(t for t in trozos if t)


def _recomendaciones(necesidades, campo, textos) -> str:
    recs = textos.get("perfil_accesibilidad", {}).get("recomendaciones", {})
    lineas = [f"- {recs[c][campo]}" for c in (necesidades or [])
              if isinstance(recs.get(c), dict) and recs[c].get(campo)]
    if not lineas:
        return ""
    return textos["orientaciones"]["encabezado_recomendaciones"] + "\n" + "\n".join(lineas)


def _juntar(*bloques: str) -> str:
    return "\n\n".join(b.strip() for b in bloques if b and b.strip())


def orientaciones(
    prog_materia=None,
    prog_destino=None,
    nivel_objetivo: str = "",
    necesidades=None,
    nombre_materia: str = "",
    curriculo_primaria=None,
    curriculo_eso=None,
) -> dict[str, str]:
    """Devuelve {apartado: texto de orientación}. Todos los argumentos son
    opcionales: con solo el nombre de la materia y el nivel ya produce algo."""
    textos = cargar_textos()
    o = textos["orientaciones"]
    cp = curriculo_primaria if curriculo_primaria is not None else cargar_curriculo_primaria()
    ce = curriculo_eso if curriculo_eso is not None else cargar_curriculo_eso()
    necesidades = necesidades or []

    nombre = (nombre_materia or getattr(prog_materia, "materia", "")
              or getattr(prog_destino, "materia", ""))

    # Competencias que se mantienen (de la programación de la materia si la hay)
    comps = getattr(prog_materia, "competencias", None) or getattr(prog_destino, "competencias", None)
    if comps:
        bloque_comps = ("Se mantienen las competencias específicas de la materia:\n" +
                        "\n".join(f"{c.numero}. {c.texto}" for c in comps))
    else:
        bloque_comps = ("No se han podido leer las competencias de la programación adjunta. "
                        "Consúltalas en el currículo oficial (abajo).")

    ref_eso = _texto_eso(nombre, ce, textos)
    ref_primaria = _texto_primaria(nombre, nivel_objetivo, textos, cp)

    # Referencia del curso destino (lo que se haya podido leer de su programación)
    ref_dest_cri = ref_dest_con = ref_dest_ins = ref_dest_met = ""
    if prog_destino is not None:
        destino = materia_desde_programacion(prog_destino)
        enc = o["encabezado_referencia_destino"]
        if destino.criterios_evaluacion:
            ref_dest_cri = f"{enc}\n{destino.criterios_evaluacion}"
        if destino.contenidos:
            ref_dest_con = f"{enc}\n{destino.contenidos}"
        if destino.instrumentos:
            ref_dest_ins = f"{enc}\n{destino.instrumentos}"
        if destino.metodologia:
            ref_dest_met = f"{enc}\n{destino.metodologia}"

    return {
        "competencias": _juntar(o["competencias"], bloque_comps, ref_eso),
        "criterios_evaluacion": _juntar(o["criterios_evaluacion"], ref_dest_cri, ref_primaria, ref_eso),
        "contenidos": _juntar(o["contenidos"], ref_dest_con, ref_primaria, ref_eso),
        "metodologia": _juntar(o["metodologia"], ref_dest_met,
                               _recomendaciones(necesidades, "metodologia", textos)),
        "instrumentos": _juntar(o["instrumentos"], ref_dest_ins,
                                _recomendaciones(necesidades, "instrumentos", textos)),
        "seguimiento": o.get("seguimiento", ""),
    }
