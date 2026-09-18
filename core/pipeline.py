"""Orquesta la adaptación completa: contenido (IA, opcional) + formato."""

from __future__ import annotations

import dataclasses
import os
from typing import Callable

from docx import Document
from docx.text.paragraph import Paragraph

from .aplicar_ia import aplicar_resultado
from .ia import Bloque, OpcionesIA, adaptar_contenido, es_cabecera_datos_alumno
from .transformador import (
    OpcionesAdaptacion,
    _es_titulo,
    _es_vineta,
    _validar_rutas,
    aplicar_formato,
)


def _terminos_glosario(datos: dict) -> list[str]:
    """Los términos que el glosario de la IA acaba de definir, listos para
    resaltarlos también en el propio texto, donde aparecen (además de la
    lista de palabras que el docente haya escrito a mano)."""
    return [
        str(entrada.get("termino", "")).strip()
        for entrada in datos.get("glosario", [])
        if str(entrada.get("termino", "")).strip()
    ]


def _extraer_bloques(
    doc, niveles_resumen: set[str] | None = None,
) -> tuple[list[Bloque], dict[int, Paragraph]]:
    """Numera los párrafos de primer nivel (no entra en tablas) y los prepara
    para enviarlos a la IA.

    `niveles_resumen`: nombres de estilo (p. ej. "Heading 2") que el docente
    ha marcado como secciones de verdad para el resumen (ver
    `core.transformador.detectar_niveles_titulo`). Si es `None`, todos los
    títulos son candidatos a resumen (comportamiento de antes, para quien no
    use la selección de niveles)."""
    bloques: list[Bloque] = []
    por_id: dict[int, Paragraph] = {}
    for i, parrafo in enumerate(doc.paragraphs):
        texto = parrafo.text.strip()
        if not texto:
            continue
        if es_cabecera_datos_alumno(texto):
            # Cabecera de examen/ficha con datos del alumno (nombre, NIA,
            # fecha de nacimiento...): nunca se manda a la IA, se deja igual.
            continue
        resumen_candidato = True
        if _es_titulo(parrafo):
            tipo = "titulo"
            if niveles_resumen is not None:
                nombre_estilo = parrafo.style.name if parrafo.style else ""
                resumen_candidato = nombre_estilo in niveles_resumen
        elif _es_vineta(parrafo) or "list" in (parrafo.style.name or "").lower():
            tipo = "lista"
        else:
            tipo = "parrafo"
        bloques.append(Bloque(id=i, tipo=tipo, texto=texto, resumen_candidato=resumen_candidato))
        por_id[i] = parrafo
    return bloques, por_id


def adaptar_documento_completo(
    ruta_entrada: str,
    ruta_salida: str,
    opciones_formato: OpcionesAdaptacion,
    opciones_ia: OpcionesIA | None = None,
    api_key: str | None = None,
    registrar: Callable[[str], None] = lambda mensaje: None,
    niveles_resumen: set[str] | None = None,
) -> dict:
    """Abre el documento, aplica (si procede) la adaptación de contenido con IA,
    luego la de formato, y guarda. Devuelve `{"ia": ..., "formato": ...}`.

    `niveles_resumen`: ver `_extraer_bloques`."""

    _validar_rutas(ruta_entrada, ruta_salida)

    registrar(f"Abriendo «{os.path.basename(ruta_entrada)}»…")
    doc = Document(ruta_entrada)

    resumen_ia: dict = {}
    opciones_formato_final = opciones_formato
    if opciones_ia is not None and opciones_ia.alguna():
        bloques, por_id = _extraer_bloques(doc, niveles_resumen)
        if not bloques:
            registrar("El documento no tiene texto que adaptar con IA.")
        else:
            datos = adaptar_contenido(bloques, opciones_ia, api_key=api_key, registrar=registrar)
            resumen_ia = aplicar_resultado(doc, datos, por_id, registrar=registrar)
            resumen_ia["_uso"] = datos.get("_uso", {})

            # Las palabras que el glosario acaba de definir se resaltan
            # también donde aparecen en el propio texto: así el alumno las
            # ve marcadas en su sitio, no solo explicadas al final -DUA:
            # varias formas de representación a la vez-.
            terminos_glosario = _terminos_glosario(datos)
            if terminos_glosario:
                opciones_formato_final = dataclasses.replace(
                    opciones_formato,
                    resaltar_palabras=list(opciones_formato.resaltar_palabras) + terminos_glosario,
                )
                registrar(f"Resaltando en el texto las {len(terminos_glosario)} palabras del glosario…")

    registrar("Aplicando el formato…")
    resumen_formato = aplicar_formato(doc, opciones_formato_final, registrar)

    carpeta = os.path.dirname(os.path.abspath(ruta_salida))
    os.makedirs(carpeta, exist_ok=True)
    doc.save(ruta_salida)
    registrar(f"Guardado en «{ruta_salida}».")

    return {"ia": resumen_ia, "formato": resumen_formato}
