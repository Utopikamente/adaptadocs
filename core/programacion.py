"""Lee una programación didáctica (.docx) y extrae los elementos curriculares
que necesita una adaptación curricular: competencias específicas, criterios de
evaluación, saberes básicos / contenidos, instrumentos de evaluación y
metodología.

Lectura **determinista y tolerante**: primero intenta la tabla habitual
«Competencias específicas | Descriptores | Criterios de evaluación»; si no
está, busca los títulos estándar de LOMLOE («Competencias específicas»,
«Criterios de evaluación», «Contenidos» o «Saberes básicos», «Instrumentos de
evaluación», «Metodología») en encabezados, párrafos o tablas, y recoge lo que
va debajo de cada uno. Solo lanza `ProgramacionNoReconocida` si no encuentra
ninguno de esos apartados.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


class ProgramacionNoReconocida(RuntimeError):
    """No se ha encontrado ningún apartado curricular en la programación."""


@dataclass
class Competencia:
    numero: str
    texto: str
    descriptores: list[str] = field(default_factory=list)
    criterios: list[tuple[str, str]] = field(default_factory=list)  # ("1.1.", "…")


@dataclass
class Programacion:
    materia: str = ""
    curso: str = ""
    competencias: list[Competencia] = field(default_factory=list)
    criterios: list[tuple[str, str]] = field(default_factory=list)      # lista plana
    saberes_basicos: dict[str, list[str]] = field(default_factory=dict)  # {"A. …": [ítems]}
    contenidos_texto: str = ""
    instrumentos: list[tuple[str, str]] = field(default_factory=list)
    instrumentos_texto: str = ""
    metodologia: str = ""


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #

def _norm(texto: str) -> str:
    """Mayúsculas sin acentos, espacios colapsados; para comparar encabezados."""
    sin = "".join(c for c in unicodedata.normalize("NFD", texto)
                  if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sin).strip().upper()


_RE_CRITERIO = re.compile(r"(?m)^\s*(\d+\.\d+\.?)\s+")
_RE_COMPETENCIA_NUM = re.compile(r"^\s*(\d+)[.\-)]?\s+(.*)", re.DOTALL)
_RE_BLOQUE = re.compile(r"^([A-Z])\.\s+(.+)")
_RE_NUM_TITULO = re.compile(r"^\s*\d+[.\)]\s*")

# título estándar -> clave de sección
_SECCIONES = {
    "COMPETENCIAS ESPECIFICAS": "competencias",
    "CRITERIOS DE EVALUACION": "criterios",
    "CONTENIDOS": "contenidos",
    "SABERES BASICOS": "contenidos",
    "INSTRUMENTOS DE EVALUACION": "instrumentos",
    "INSTRUMENTOS Y CRITERIOS DE CALIFICACION": "instrumentos",
    "CRITERIOS DE CALIFICACION": "instrumentos",
    "METODOLOGIA": "metodologia",
}


def _trocear_criterios(texto: str) -> list[tuple[str, str]]:
    """De un texto con «1.1. … 1.2. …» saca [("1.1.", "…"), ("1.2.", "…")]."""
    marcas = list(_RE_CRITERIO.finditer(texto))
    if not marcas:
        limpio = " ".join(texto.split())
        return [("", limpio)] if limpio else []
    salida: list[tuple[str, str]] = []
    for i, m in enumerate(marcas):
        ini = m.end()
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        codigo = m.group(1)
        if not codigo.endswith("."):
            codigo += "."
        cuerpo = " ".join(texto[ini:fin].split())
        if cuerpo:
            salida.append((codigo, cuerpo))
    return salida


def _descriptores(texto: str) -> list[str]:
    return [p.strip() for p in re.split(r"[/\n,;]+", texto) if p.strip()]


def _parsear_saberes(texto: str) -> dict[str, list[str]]:
    bloques: dict[str, list[str]] = {}
    actual: str | None = None
    for linea in texto.splitlines():
        t = linea.strip()
        if not t:
            continue
        m = _RE_BLOQUE.match(t)
        if m:
            actual = f"{m.group(1)}. {m.group(2).strip()}"
            bloques.setdefault(actual, [])
        elif actual:
            bloques[actual].append(re.sub(r"^[-–·]\s*", "", t))
        else:
            bloques.setdefault("(sin bloque)", []).append(re.sub(r"^[-–·]\s*", "", t))
    return bloques


def _competencias_de_texto(texto: str) -> list[Competencia]:
    comps: list[Competencia] = []
    actual: Competencia | None = None
    for linea in texto.splitlines():
        t = linea.strip()
        if not t:
            continue
        m = re.match(r"^(\d+)[.\-)]\s+(.{15,})", t)
        if m:
            if actual:
                comps.append(actual)
            actual = Competencia(numero=m.group(1), texto=m.group(2).strip())
        elif actual and not _RE_CRITERIO.match(t):
            actual.texto = (actual.texto + " " + t).strip()
    if actual:
        comps.append(actual)
    for c in comps:
        c.texto = " ".join(c.texto.split())
    return comps


def _buscar_tabla(doc, *encabezados_requeridos: str):
    objetivo = [_norm(e) for e in encabezados_requeridos]
    for tabla in doc.tables:
        if not tabla.rows:
            continue
        cabecera = " | ".join(_norm(c.text) for c in tabla.rows[0].cells)
        if all(e in cabecera for e in objetivo):
            return tabla
    return None


def _celdas_unicas(fila):
    vistos, salida = set(), []
    for c in fila.cells:
        if id(c._tc) in vistos:
            continue
        vistos.add(id(c._tc))
        salida.append(c)
    return salida


# --------------------------------------------------------------------------- #
# Vía preferente: la tabla de 3 columnas
# --------------------------------------------------------------------------- #

def _parsear_tabla_centro(prog: Programacion, tabla) -> None:
    modo_saberes = False
    for fila in tabla.rows[1:]:
        celdas = _celdas_unicas(fila)
        textos = [c.text.strip() for c in celdas]
        if not any(textos):
            continue
        if _norm(textos[0]).startswith(("SABERES BASICOS", "CONTENIDOS")):
            modo_saberes = True
            continue
        if modo_saberes:
            prog.saberes_basicos = _parsear_saberes(celdas[0].text)
            modo_saberes = False
            continue
        m = _RE_COMPETENCIA_NUM.match(textos[0])
        if not m:
            continue
        comp = Competencia(numero=m.group(1), texto=" ".join(m.group(2).split()))
        if len(celdas) >= 3:
            comp.descriptores = _descriptores(celdas[1].text)
            comp.criterios = _trocear_criterios(celdas[2].text)
        elif len(celdas) == 2:
            comp.criterios = _trocear_criterios(celdas[1].text)
        prog.competencias.append(comp)


# --------------------------------------------------------------------------- #
# Vía tolerante: buscar títulos estándar por el documento
# --------------------------------------------------------------------------- #

def _iter_bloques(doc):
    """Recorre el cuerpo en orden y devuelve ('p', texto) o ('tbl', Table)."""
    parent = doc.element.body
    for hijo in parent.iterchildren():
        if hijo.tag == qn("w:p"):
            yield "p", Paragraph(hijo, doc).text
        elif hijo.tag == qn("w:tbl"):
            yield "tbl", Table(hijo, doc)


def _clave_seccion(texto: str) -> str | None:
    t = _norm(_RE_NUM_TITULO.sub("", texto)).rstrip(" .:")
    if len(t) > 90:
        return None
    for titulo, clave in _SECCIONES.items():
        if t == titulo or t.startswith(titulo):
            return clave
    return None


def _texto_de_tabla(tabla) -> str:
    filas = []
    for fila in tabla.rows:
        filas.append("  ".join(c.text.strip() for c in _celdas_unicas(fila)))
    return "\n".join(filas)


def _parsear_tolerante(doc, prog: Programacion) -> None:
    secciones: dict[str, list[str]] = {}
    actual: str | None = None
    for tipo, contenido in _iter_bloques(doc):
        if tipo == "p":
            clave = _clave_seccion(contenido) if contenido.strip() else None
            if clave:
                actual = clave
                secciones.setdefault(clave, [])
                continue
            if actual:
                secciones[actual].append(contenido)
        else:  # tabla
            cab = " | ".join(_norm(c.text) for c in tabla_cab(contenido))
            clave = next((k for t, k in _SECCIONES.items() if t in cab), None)
            destino = clave or actual
            if destino:
                secciones.setdefault(destino, [])
                secciones[destino].append(_texto_de_tabla(contenido))

    def _texto(clave: str) -> str:
        return "\n".join(secciones.get(clave, [])).strip()

    if _texto("competencias"):
        prog.competencias = _competencias_de_texto(_texto("competencias"))
    crit = _texto("criterios") or _texto("competencias")
    prog.criterios = [(c, t) for c, t in _trocear_criterios(crit) if c]
    if _texto("contenidos"):
        prog.saberes_basicos = _parsear_saberes(_texto("contenidos"))
        prog.contenidos_texto = _texto("contenidos")
    if _texto("instrumentos"):
        prog.instrumentos_texto = _texto("instrumentos")
    if _texto("metodologia"):
        prog.metodologia = _texto("metodologia")


def tabla_cab(tabla):
    return _celdas_unicas(tabla.rows[0]) if tabla.rows else []


# --------------------------------------------------------------------------- #

def leer_programacion(ruta: str, *, materia: str = "", curso: str = "") -> Programacion:
    """Extrae de `ruta` (un .docx) la información curricular disponible. Lanza
    `ProgramacionNoReconocida` solo si no encuentra ningún apartado."""
    doc = Document(ruta)
    prog = Programacion(materia=materia, curso=curso)

    tabla = _buscar_tabla(doc, "COMPETENCIAS ESPECIFICAS", "CRITERIOS DE EVALUACION")
    if tabla is not None:
        _parsear_tabla_centro(prog, tabla)
    else:
        _parsear_tolerante(doc, prog)

    if not prog.instrumentos and not prog.instrumentos_texto:
        tabla_inst = _buscar_tabla(doc, "INSTRUMENTO DE EVALUACION")
        if tabla_inst is not None:
            for fila in tabla_inst.rows[1:]:
                celdas = _celdas_unicas(fila)
                if len(celdas) >= 2 and (celdas[0].text.strip() or celdas[1].text.strip()):
                    prog.instrumentos.append((celdas[0].text.strip(), celdas[1].text.strip()))

    if not (prog.competencias or prog.criterios or prog.saberes_basicos
            or prog.contenidos_texto or prog.instrumentos or prog.instrumentos_texto):
        raise ProgramacionNoReconocida(
            "No se ha encontrado ningún apartado de competencias, criterios, "
            "contenidos o instrumentos en la programación."
        )
    return prog
