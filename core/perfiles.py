"""Perfiles de adaptación predefinidos.

Cada perfil es un punto de partida razonable. En la ventana se pueden
retocar todas las opciones antes de generar el documento.
"""

from __future__ import annotations

from .transformador import OpcionesAdaptacion

PERFIL_POR_DEFECTO = "General (lectura fácil)"

PERFILES: dict[str, OpcionesAdaptacion] = {
    "General (lectura fácil)": OpcionesAdaptacion(
        fuente="Verdana",
        tamano_pt=14,
        interlineado=1.5,
        espacio_despues_pt=10,
        alinear_izquierda=True,
        margenes_cm=2.5,
        una_columna=True,
        alto_contraste=True,
        negrita_titulos=True,
    ),
    "Dislexia": OpcionesAdaptacion(
        fuente="Verdana",
        tamano_pt=14,
        interlineado=1.5,
        espacio_despues_pt=12,
        alinear_izquierda=True,
        margenes_cm=3.0,
        una_columna=True,
        alto_contraste=True,
        negrita_titulos=True,
    ),
    "TDAH": OpcionesAdaptacion(
        fuente="Verdana",
        tamano_pt=13,
        interlineado=1.5,
        espacio_despues_pt=14,
        alinear_izquierda=True,
        margenes_cm=3.0,
        una_columna=True,
        alto_contraste=True,
        negrita_titulos=True,
        convertir_vinetas_en_pasos=True,
    ),
    "TEA": OpcionesAdaptacion(
        fuente="Arial",
        tamano_pt=13,
        interlineado=1.5,
        espacio_despues_pt=12,
        alinear_izquierda=True,
        margenes_cm=2.5,
        una_columna=True,
        alto_contraste=True,
        negrita_titulos=True,
        convertir_vinetas_en_pasos=True,
    ),
    "Discapacidad intelectual leve": OpcionesAdaptacion(
        fuente="Arial",
        tamano_pt=16,
        interlineado=2.0,
        espacio_despues_pt=16,
        alinear_izquierda=True,
        margenes_cm=3.0,
        una_columna=True,
        alto_contraste=True,
        negrita_titulos=True,
        convertir_vinetas_en_pasos=True,
    ),
    "Baja visión": OpcionesAdaptacion(
        fuente="Arial",
        tamano_pt=18,
        interlineado=2.0,
        espacio_despues_pt=18,
        alinear_izquierda=True,
        margenes_cm=2.0,
        una_columna=True,
        alto_contraste=True,
        negrita_titulos=True,
    ),
}


def opciones_de_perfil(nombre: str) -> OpcionesAdaptacion:
    """Devuelve una copia editable de las opciones de un perfil."""
    return PERFILES.get(nombre, PERFILES[PERFIL_POR_DEFECTO]).copia()
