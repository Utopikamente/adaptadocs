"""Guardado seguro de la clave de API en el almacén de credenciales del sistema
(Administrador de credenciales de Windows, Llavero de macOS, etc.) mediante
`keyring`. Si `keyring` no está disponible, se recurre a la variable de entorno
ANTHROPIC_API_KEY (solo lectura)."""

from __future__ import annotations

import os

_SERVICIO = "adaptadocs"
_USUARIO = "anthropic-api-key"

try:  # keyring es opcional
    import keyring

    _HAY_KEYRING = True
except Exception:  # pragma: no cover
    keyring = None  # type: ignore
    _HAY_KEYRING = False


def hay_almacen() -> bool:
    return _HAY_KEYRING


def leer_clave() -> str | None:
    if _HAY_KEYRING:
        try:
            guardada = keyring.get_password(_SERVICIO, _USUARIO)
            if guardada:
                return guardada
        except Exception:
            pass
    return os.environ.get("ANTHROPIC_API_KEY") or None


def guardar_clave(clave: str) -> bool:
    if not clave or not _HAY_KEYRING:
        return False
    try:
        keyring.set_password(_SERVICIO, _USUARIO, clave)
        return True
    except Exception:
        return False


def borrar_clave() -> None:
    if not _HAY_KEYRING:
        return
    try:
        keyring.delete_password(_SERVICIO, _USUARIO)
    except Exception:
        pass
