"""Pictogramas de apoyo desde ARASAAC.

Solo se usa si el usuario activa la opción. Envía a ARASAAC **únicamente las
palabras a ilustrar** (no el documento) y descarga los pictogramas. Requiere
conexión.

Licencia de los pictogramas: CC BY-NC-SA. Autor: Sergio Palao. Procedencia:
ARASAAC (https://arasaac.org). Propiedad del Gobierno de Aragón.
"""

from __future__ import annotations

import json
import os
import tempfile
import urllib.parse
import urllib.request

_API_BUSQUEDA = "https://api.arasaac.org/api/pictograms/es/search/{}"
_IMAGEN = "https://static.arasaac.org/pictograms/{pid}/{pid}_300.png"
_TIMEOUT = 8
_UA = "Adaptadocs (herramienta educativa; https://github.com/Utopikamente/adaptadocs)"

ATRIBUCION = (
    "Pictogramas: ARASAAC (arasaac.org). Autor: Sergio Palao. "
    "Licencia CC BY-NC-SA. Propiedad del Gobierno de Aragón."
)


def _carpeta_cache() -> str:
    base = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    ruta = os.path.join(base, "adaptadocs", "pictogramas")
    os.makedirs(ruta, exist_ok=True)
    return ruta


def _descargar(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(peticion, timeout=_TIMEOUT) as respuesta:  # noqa: S310
        return respuesta.read()


def _buscar_id(palabra: str) -> int | None:
    url = _API_BUSQUEDA.format(urllib.parse.quote(palabra.strip()))
    try:
        datos = json.loads(_descargar(url).decode("utf-8"))
    except Exception:
        return None
    if isinstance(datos, list) and datos:
        pid = datos[0].get("_id")
        try:
            return int(pid)
        except (TypeError, ValueError):
            return None
    return None


def obtener(palabra: str) -> bytes | None:
    """PNG del pictograma de `palabra`, o None si no hay o no hay conexión.
    Cachea los aciertos en disco."""
    clave = palabra.strip().lower()
    if not clave:
        return None

    nombre = urllib.parse.quote(clave, safe="") + ".png"
    cache = os.path.join(_carpeta_cache(), nombre)
    if os.path.isfile(cache):
        try:
            with open(cache, "rb") as f:
                return f.read()
        except OSError:
            pass

    pid = _buscar_id(clave)
    if pid is None:
        return None
    try:
        png = _descargar(_IMAGEN.format(pid=pid))
    except Exception:
        return None

    try:
        with open(cache, "wb") as f:
            f.write(png)
    except OSError:
        pass
    return png
