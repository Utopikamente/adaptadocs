"""Lee una programación didáctica (.docx) y extrae los elementos curriculares
que necesita una adaptación curricular: competencias específicas, criterios de
evaluación (por competencia), saberes básicos / contenidos (por bloque) e
instrumentos de evaluación.

Lectura **determinista**, pensada para la plantilla habitual de programación
(dos tablas: una con columnas «Competencias específicas | Descriptores |
Criterios de evaluación» y una fila «Saberes básicos»; otra con «Elemento |
Instrumento de evaluación»). Si la programación no trae esas tablas, se lanza
`ProgramacionNoReconocida` para que quien llame decida otra vía (p. ej. IA).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from docx import Document


class ProgramacionNoReconocida(RuntimeError):
    """La programación no tiene la estructura de tablas esperada."""


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
    saberes_basicos: dict[str, list[str]] = field(default_factory=dict)  # {"A. …": [ítems]}
    instrumentos: list[tuple[str, str]] = field(default_factory=list)    # ("Listening", "Prueba escrita")


# --------------------------------------------------------------------------- #

def _norm(texto: str) -> str:
    """Mayúsculas sin acentos, espacios colapsados; para comparar encabezados."""
    sin = "".join(c for c in unicodedata.normalize("NFD", texto)
                  if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sin).strip().upper()


_RE_CRITERIO = re.compile(r"(?m)^\s*(\d+\.\d+\.?)\s+")
_RE_COMPETENCIA_NUM = re.compile(r"^\s*(\d+)[.\-)]?\s+(.*)", re.DOTALL)
_RE_BLOQUE = re.compile(r"^([A-Z])\.\s+(.+)")


def _trocear_criterios(celda_texto: str) -> list[tuple[str, str]]:
    """De un texto con «1.1. … 1.2. …» saca [("1.1.", "…"), ("1.2.", "…")]."""
    marcas = list(_RE_CRITERIO.finditer(celda_texto))
    if not marcas:
        limpio = " ".join(celda_texto.split())
        return [("", limpio)] if limpio else []
    salida: list[tuple[str, str]] = []
    for i, m in enumerate(marcas):
        ini = m.end()
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(celda_texto)
        codigo = m.group(1)
        if not codigo.endswith("."):
            codigo += "."
        texto = " ".join(celda_texto[ini:fin].split())
        if texto:
            salida.append((codigo, texto))
    return salida


def _descriptores(celda_texto: str) -> list[str]:
    partes = re.split(r"[/\n,;]+", celda_texto)
    return [p.strip() for p in partes if p.strip()]


def _parsear_saberes(celda_texto: str) -> dict[str, list[str]]:
    bloques: dict[str, list[str]] = {}
    actual: str | None = None
    for linea in celda_texto.splitlines():
        t = linea.strip()
        if not t:
            continue
        m = _RE_BLOQUE.match(t)
        if m:
            actual = f"{m.group(1)}. {m.group(2).strip()}"
            bloques.setdefault(actual, [])
        elif actual:
            bloques[actual].append(t)
        else:
            bloques.setdefault("(sin bloque)", []).append(t)
    return bloques


def _buscar_tabla(doc, *encabezados_requeridos: str):
    """Devuelve la primera tabla cuya primera fila contiene TODOS los
    encabezados dados (comparación normalizada)."""
    objetivo = [_norm(e) for e in encabezados_requeridos]
    for tabla in doc.tables:
        if not tabla.rows:
            continue
        cabecera = " | ".join(_norm(c.text) for c in tabla.rows[0].cells)
        if all(e in cabecera for e in objetivo):
            return tabla
    return None


def _celdas_unicas(fila):
    vistos = set()
    salida = []
    for c in fila.cells:
        if id(c._tc) in vistos:
            continue
        vistos.add(id(c._tc))
        salida.append(c)
    return salida


# --------------------------------------------------------------------------- #

def leer_programacion(ruta: str, *, materia: str = "", curso: str = "") -> Programacion:
    """Extrae de `ruta` (un .docx) la información curricular. Lanza
    `ProgramacionNoReconocida` si no encuentra la tabla de competencias y
    criterios."""
    doc = Document(ruta)
    prog = Programacion(materia=materia, curso=curso)

    tabla = _buscar_tabla(doc, "COMPETENCIAS ESPECIFICAS", "CRITERIOS DE EVALUACION")
    if tabla is None:
        raise ProgramacionNoReconocida(
            "No se ha encontrado la tabla «Competencias específicas | … | "
            "Criterios de evaluación» en la programación."
        )

    modo_saberes = False
    for fila in tabla.rows[1:]:
        celdas = _celdas_unicas(fila)
        textos = [c.text.strip() for c in celdas]
        if not any(textos):
            continue

        if _norm(textos[0]).startswith("SABERES BASICOS") or _norm(textos[0]).startswith("CONTENIDOS"):
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

    tabla_inst = _buscar_tabla(doc, "INSTRUMENTO DE EVALUACION")
    if tabla_inst is not None:
        for fila in tabla_inst.rows[1:]:
            celdas = _celdas_unicas(fila)
            if len(celdas) >= 2 and (celdas[0].text.strip() or celdas[1].text.strip()):
                prog.instrumentos.append(
                    (celdas[0].text.strip(), celdas[1].text.strip())
                )

    return prog
