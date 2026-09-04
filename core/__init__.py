"""Núcleo del adaptador de documentos Word."""

from .transformador import OpcionesAdaptacion, adaptar_documento
from .perfiles import PERFILES, PERFIL_POR_DEFECTO

__all__ = [
    "OpcionesAdaptacion",
    "adaptar_documento",
    "PERFILES",
    "PERFIL_POR_DEFECTO",
]
