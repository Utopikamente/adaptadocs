"""Orquesta la adaptación completa: contenido (IA, opcional) + formato."""

from __future__ import annotations

import os
from typing import Callable

from docx import Document
from docx.text.paragraph import Paragraph

from .aplicar_ia import aplicar_resultado
from .ia import Bloque, OpcionesIA, adaptar_contenido
from .transformador import (
    OpcionesAdaptacion,
    _es_titulo,
    _es_vineta,
    _validar_rutas,
    aplicar_formato,
)


def _extraer_bloques(doc) -> tuple[list[Bloque], dict[int, Paragraph]]:
    """Numera los párrafos de primer nivel (no entra en tablas) y los prepara
    para enviarlos a la IA."""
    bloques: list[Bloque] = []
    por_id: dict[int, Paragraph] = {}
    for i, parrafo in enumerate(doc.paragraphs):
        texto = parrafo.text.strip()
        if not texto:
            continue
        if _es_titulo(parrafo):
            tipo = "titulo"
        elif _es_vineta(parrafo) or "list" in (parrafo.style.name or "").lower():
            tipo = "lista"
        else:
            tipo = "parrafo"
        bloques.append(Bloque(id=i, tipo=tipo, texto=texto))
        por_id[i] = parrafo
    return bloques, por_id


def adaptar_documento_completo(
    ruta_entrada: str,
    ruta_salida: str,
    opciones_formato: OpcionesAdaptacion,
    opciones_ia: OpcionesIA | None = None,
    api_key: str | None = None,
    registrar: Callable[[str], None] = lambda mensaje: None,
) -> dict:
    """Abre el documento, aplica (si procede) la adaptación de contenido con IA,
    luego la de formato, y guarda. Devuelve `{"ia": ..., "formato": ...}`."""

    _validar_rutas(ruta_entrada, ruta_salida)

    registrar(f"Abriendo «{os.path.basename(ruta_entrada)}»…")
    doc = Document(ruta_entrada)

    resumen_ia: dict = {}
    if opciones_ia is not None and opciones_ia.alguna():
        bloques, por_id = _extraer_bloques(doc)
        if not bloques:
            registrar("El documento no tiene texto que adaptar con IA.")
        else:
            datos = adaptar_contenido(bloques, opciones_ia, api_key=api_key, registrar=registrar)
            resumen_ia = aplicar_resultado(doc, datos, por_id, registrar=registrar)
            resumen_ia["_uso"] = datos.get("_uso", {})

    registrar("Aplicando el formato…")
    resumen_formato = aplicar_formato(doc, opciones_formato, registrar)

    carpeta = os.path.dirname(os.path.abspath(ruta_salida))
    os.makedirs(carpeta, exist_ok=True)
    doc.save(ruta_salida)
    registrar(f"Guardado en «{ruta_salida}».")

    return {"ia": resumen_ia, "formato": resumen_formato}
