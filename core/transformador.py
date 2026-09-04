"""Transformaciones de formato sobre documentos .docx.

Todo lo que hay aquí es determinista: no llama a ningún servicio externo ni
modifica el contenido del texto (salvo resaltar palabras). Solo cambia el
aspecto del documento para hacerlo más legible.
"""

from __future__ import annotations

import os
import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run


# --------------------------------------------------------------------------- #
# Opciones
# --------------------------------------------------------------------------- #

COLORES_RESALTADO = {
    "AMARILLO": WD_COLOR_INDEX.YELLOW,
    "VERDE": WD_COLOR_INDEX.BRIGHT_GREEN,
    "TURQUESA": WD_COLOR_INDEX.TURQUOISE,
    "ROSA": WD_COLOR_INDEX.PINK,
    "GRIS": WD_COLOR_INDEX.GRAY_25,
}


@dataclass
class OpcionesAdaptacion:
    """Conjunto de ajustes de formato que se aplican a un documento."""

    # Tipografía
    fuente: str | None = "Verdana"
    tamano_pt: float | None = 14.0

    # Espaciado
    interlineado: float | None = 1.5
    espacio_despues_pt: float | None = 10.0

    # Disposición
    alinear_izquierda: bool = True          # convierte el texto justificado en alineado a la izquierda
    margenes_cm: float | None = 2.5         # None = no tocar los márgenes
    una_columna: bool = True                # fuerza una sola columna
    alto_contraste: bool = True             # pone todo el texto en negro

    # Ayudas visuales
    negrita_titulos: bool = True
    convertir_vinetas_en_pasos: bool = False
    resaltar_palabras: list[str] = field(default_factory=list)
    color_resaltado: str = "AMARILLO"

    def copia(self) -> "OpcionesAdaptacion":
        return deepcopy(self)


# --------------------------------------------------------------------------- #
# Utilidades de recorrido
# --------------------------------------------------------------------------- #

def _iter_parrafos(contenedor) -> Iterator[Paragraph]:
    """Devuelve todos los párrafos de un contenedor (documento, celda,
    cabecera o pie), entrando también en las tablas anidadas."""
    for parrafo in contenedor.paragraphs:
        yield parrafo
    for tabla in contenedor.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                yield from _iter_parrafos(celda)


def _contenedores(doc) -> Iterable:
    yield doc
    for seccion in doc.sections:
        yield seccion.header
        yield seccion.first_page_header
        yield seccion.even_page_header
        yield seccion.footer
        yield seccion.first_page_footer
        yield seccion.even_page_footer


# --------------------------------------------------------------------------- #
# Fuente
# --------------------------------------------------------------------------- #

def _forzar_rfonts(rpr, fuente: str) -> None:
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), fuente)


def _formatear_run(run: Run, o: OpcionesAdaptacion) -> None:
    if o.fuente:
        run.font.name = o.fuente
        _forzar_rfonts(run._element.get_or_add_rPr(), o.fuente)
    if o.tamano_pt:
        run.font.size = Pt(o.tamano_pt)
    if o.alto_contraste:
        run.font.color.rgb = RGBColor(0, 0, 0)


# --------------------------------------------------------------------------- #
# Párrafo
# --------------------------------------------------------------------------- #

_PREFIJOS_TITULO = ("heading", "título", "titulo", "subtitle", "subtítulo")
_MARCAS_VINETA = ("bullet", "viñeta", "vineta", "list bullet")


def _es_titulo(parrafo: Paragraph) -> bool:
    nombre = (parrafo.style.name or "").lower() if parrafo.style else ""
    return any(nombre.startswith(p) for p in _PREFIJOS_TITULO)


def _es_vineta(parrafo: Paragraph) -> bool:
    nombre = (parrafo.style.name or "").lower() if parrafo.style else ""
    return any(m in nombre for m in _MARCAS_VINETA)


def _formatear_parrafo(parrafo: Paragraph, o: OpcionesAdaptacion) -> None:
    pf = parrafo.paragraph_format
    if o.interlineado:
        pf.line_spacing = float(o.interlineado)
    if o.espacio_despues_pt is not None:
        pf.space_after = Pt(o.espacio_despues_pt)
    if o.alinear_izquierda and parrafo.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
        parrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT


# --------------------------------------------------------------------------- #
# Resaltado de palabras clave
# --------------------------------------------------------------------------- #

def _clonar_run(base: Run, texto: str, ancla: Run) -> Run:
    nuevo_el = deepcopy(base._element)
    ancla._element.addnext(nuevo_el)
    nuevo = Run(nuevo_el, base._parent)
    nuevo.text = texto
    return nuevo


def _resaltar_en_parrafo(parrafo: Paragraph, patron: re.Pattern, color) -> int:
    """Divide los runs para poder marcar solo las palabras buscadas.
    Devuelve el número de coincidencias resaltadas."""
    total = 0
    for run in list(parrafo.runs):
        texto = run.text
        if not texto:
            continue
        trozos = patron.split(texto)
        if len(trozos) == 1:
            continue
        run.text = trozos[0]
        ancla = run
        for i, trozo in enumerate(trozos[1:], start=1):
            if trozo == "":
                continue
            nuevo = _clonar_run(run, trozo, ancla)
            if i % 2 == 1:                       # los índices impares son coincidencias
                nuevo.font.highlight_color = color
                total += 1
            else:
                nuevo.font.highlight_color = None
            ancla = nuevo
    return total


def _compilar_patron(palabras: list[str]) -> re.Pattern | None:
    limpias = [p.strip() for p in palabras if p and p.strip()]
    if not limpias:
        return None
    alternativas = "|".join(re.escape(p) for p in sorted(limpias, key=len, reverse=True))
    return re.compile(f"({alternativas})", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Secciones (márgenes y columnas)
# --------------------------------------------------------------------------- #

def _una_columna(seccion) -> None:
    sectPr = seccion._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        return
    cols.set(qn("w:num"), "1")
    for hijo in list(cols):
        cols.remove(hijo)


def _ajustar_seccion(seccion, o: OpcionesAdaptacion) -> None:
    if o.margenes_cm is not None:
        margen = Cm(o.margenes_cm)
        seccion.left_margin = margen
        seccion.right_margin = margen
        seccion.top_margin = margen
        seccion.bottom_margin = margen
    if o.una_columna:
        _una_columna(seccion)


# --------------------------------------------------------------------------- #
# Estilo Normal
# --------------------------------------------------------------------------- #

def _ajustar_estilo_normal(doc, o: OpcionesAdaptacion) -> None:
    try:
        normal = doc.styles["Normal"]
    except KeyError:
        return
    if o.fuente:
        normal.font.name = o.fuente
        _forzar_rfonts(normal.element.get_or_add_rPr(), o.fuente)
    if o.tamano_pt:
        normal.font.size = Pt(o.tamano_pt)
    pf = normal.paragraph_format
    if o.interlineado:
        pf.line_spacing = float(o.interlineado)
    if o.espacio_despues_pt is not None:
        pf.space_after = Pt(o.espacio_despues_pt)


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #

def adaptar_documento(
    ruta_entrada: str,
    ruta_salida: str,
    opciones: OpcionesAdaptacion,
    registrar: Callable[[str], None] = lambda mensaje: None,
) -> dict:
    """Lee `ruta_entrada`, aplica `opciones` y guarda el resultado en
    `ruta_salida`. Devuelve un pequeño resumen de lo que se ha hecho."""

    ext = os.path.splitext(ruta_entrada)[1].lower()
    if ext == ".doc":
        raise ValueError(
            "El formato .doc (Word 97-2003) no es compatible. "
            "Abre el archivo en Word y guárdalo como .docx."
        )
    if ext != ".docx":
        raise ValueError(f"Se esperaba un archivo .docx y se recibió «{ext or 'sin extensión'}».")
    if os.path.abspath(ruta_entrada) == os.path.abspath(ruta_salida):
        raise ValueError("El archivo de salida no puede ser el mismo que el de entrada.")

    registrar(f"Abriendo «{os.path.basename(ruta_entrada)}»…")
    doc = Document(ruta_entrada)

    resumen = {"parrafos": 0, "runs": 0, "resaltados": 0, "vinetas_convertidas": 0}

    _ajustar_estilo_normal(doc, opciones)
    for seccion in doc.sections:
        _ajustar_seccion(seccion, opciones)

    patron = _compilar_patron(opciones.resaltar_palabras)
    color = COLORES_RESALTADO.get(opciones.color_resaltado.upper(), WD_COLOR_INDEX.YELLOW)

    for contenedor in _contenedores(doc):
        for parrafo in _iter_parrafos(contenedor):
            resumen["parrafos"] += 1

            if opciones.convertir_vinetas_en_pasos and _es_vineta(parrafo):
                try:
                    parrafo.style = doc.styles["List Number"]
                    resumen["vinetas_convertidas"] += 1
                except KeyError:
                    pass

            _formatear_parrafo(parrafo, opciones)

            es_titulo = opciones.negrita_titulos and _es_titulo(parrafo)
            for run in parrafo.runs:
                _formatear_run(run, opciones)
                if es_titulo:
                    run.bold = True
                resumen["runs"] += 1

            if patron is not None:
                resumen["resaltados"] += _resaltar_en_parrafo(parrafo, patron, color)

    carpeta = os.path.dirname(os.path.abspath(ruta_salida))
    os.makedirs(carpeta, exist_ok=True)
    doc.save(ruta_salida)
    registrar(f"Guardado en «{ruta_salida}».")

    return resumen
