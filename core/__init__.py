"""Núcleo de Adaptadocs (adaptación de documentos .docx)."""

from .perfiles import PERFILES, PERFIL_POR_DEFECTO, opciones_de_perfil
from .transformador import OpcionesAdaptacion, adaptar_documento, aplicar_formato
from .ia import MODELOS, NIVELES, MODELO_POR_DEFECTO, NIVEL_POR_DEFECTO, OpcionesIA
from .pipeline import adaptar_documento_completo

__all__ = [
    "OpcionesAdaptacion",
    "adaptar_documento",
    "aplicar_formato",
    "PERFILES",
    "PERFIL_POR_DEFECTO",
    "opciones_de_perfil",
    "OpcionesIA",
    "MODELOS",
    "NIVELES",
    "MODELO_POR_DEFECTO",
    "NIVEL_POR_DEFECTO",
    "adaptar_documento_completo",
]
