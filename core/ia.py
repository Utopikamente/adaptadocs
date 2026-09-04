"""Adaptación de *contenido* con IA (Claude / API de Anthropic).

A diferencia de `transformador.py`, este módulo **sí** envía el texto del
documento a un servicio externo (la API de Anthropic) para reescribirlo y
generar apoyos. Requiere una clave de API.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Callable

# --------------------------------------------------------------------------- #
# Catálogos para la interfaz
# --------------------------------------------------------------------------- #

MODELOS: dict[str, str] = {
    "Opus 5 — máxima calidad": "claude-opus-5",
    "Sonnet 5 — equilibrado, más barato": "claude-sonnet-5",
    "Haiku 4.5 — rápido y económico": "claude-haiku-4-5",
}
MODELO_POR_DEFECTO = "Opus 5 — máxima calidad"

NIVELES: dict[str, str] = {
    "1º-2º de Primaria": "unos 6-7 años; frases muy cortas (máximo 8-10 palabras), "
    "vocabulario básico del día a día, nada de subordinadas",
    "3º-4º de Primaria": "unos 8-9 años; frases cortas (máximo 12 palabras), "
    "vocabulario sencillo, una idea por frase",
    "5º-6º de Primaria": "unos 10-11 años; frases de máximo 15 palabras, "
    "vocabulario común, se puede usar algún término académico si se explica",
    "1º-2º de ESO": "unos 12-13 años; frases claras y directas, se admite vocabulario "
    "académico siempre que se explique la primera vez",
    "Lectura fácil (adultos)": "pautas de Lectura Fácil: cada frase una sola idea, "
    "voz activa, orden sujeto-verbo-predicado, sin metáforas ni dobles sentidos",
}
NIVEL_POR_DEFECTO = "5º-6º de Primaria"


# --------------------------------------------------------------------------- #
# Opciones y bloques
# --------------------------------------------------------------------------- #

@dataclass
class OpcionesIA:
    simplificar: bool = False
    glosario: bool = False
    resumen: bool = False
    preguntas: bool = False
    pasos: bool = False
    nivel: str = NIVEL_POR_DEFECTO
    modelo: str = "claude-opus-5"
    n_preguntas: int = 5

    def alguna(self) -> bool:
        return any(
            (self.simplificar, self.glosario, self.resumen, self.preguntas, self.pasos)
        )


@dataclass
class Bloque:
    """Un fragmento del documento que se manda a la IA."""

    id: int
    tipo: str  # "titulo" | "parrafo" | "lista"
    texto: str


# --------------------------------------------------------------------------- #
# Esquema de respuesta (JSON estructurado)
# --------------------------------------------------------------------------- #

def _esquema() -> dict:
    obj = lambda props, req: {  # noqa: E731
        "type": "object",
        "additionalProperties": False,
        "required": req,
        "properties": props,
    }
    return {
        "type": "json_schema",
        "schema": obj(
            {
                "parrafos_simplificados": {
                    "type": "array",
                    "items": obj(
                        {"id": {"type": "integer"}, "texto": {"type": "string"}},
                        ["id", "texto"],
                    ),
                },
                "parrafos_en_pasos": {
                    "type": "array",
                    "items": obj(
                        {
                            "id": {"type": "integer"},
                            "pasos": {"type": "array", "items": {"type": "string"}},
                        },
                        ["id", "pasos"],
                    ),
                },
                "glosario": {
                    "type": "array",
                    "items": obj(
                        {
                            "termino": {"type": "string"},
                            "definicion": {"type": "string"},
                        },
                        ["termino", "definicion"],
                    ),
                },
                "resumen": {
                    "type": "array",
                    "items": obj(
                        {
                            "apartado": {"type": "string"},
                            "puntos": {"type": "array", "items": {"type": "string"}},
                        },
                        ["apartado", "puntos"],
                    ),
                },
                "preguntas": {"type": "array", "items": {"type": "string"}},
            },
            [
                "parrafos_simplificados",
                "parrafos_en_pasos",
                "glosario",
                "resumen",
                "preguntas",
            ],
        ),
    }


_SISTEMA = (
    "Eres un especialista en adaptación curricular y lectura fácil para alumnado "
    "con dificultades de aprendizaje. Adaptas materiales escolares sin perder "
    "información: conservas los datos, las cifras, los nombres propios y el "
    "sentido original. Nunca inventas contenido que no esté en el texto. "
    "Escribes siempre en el mismo idioma que el documento original (español). "
    "Devuelves únicamente el JSON que se te pide, sin comentarios."
)


def _mensaje_usuario(bloques: list[Bloque], o: OpcionesIA) -> str:
    lineas: list[str] = [
        "DOCUMENTO. Cada bloque lleva su identificador entre corchetes y su tipo:",
        "",
    ]
    for b in bloques:
        lineas.append(f"[{b.id}] ({b.tipo}) {b.texto}")
    lineas += [
        "",
        f"NIVEL DE LECTURA OBJETIVO: {o.nivel} — {NIVELES.get(o.nivel, '')}.",
        "",
        "TAREAS. Rellena en el JSON SOLO las claves de las tareas pedidas; "
        "deja el resto como listas vacías.",
    ]
    if o.simplificar:
        lineas.append(
            "- parrafos_simplificados: reescribe al nivel objetivo SOLO los bloques "
            "(parrafo) y (lista). No toques los (titulo). Devuelve un elemento por "
            "bloque que cambies, con su id y el texto nuevo. Si un bloque ya es "
            "suficientemente sencillo, no lo incluyas."
        )
    if o.pasos:
        lineas.append(
            "- parrafos_en_pasos: para los bloques (parrafo) que expliquen un "
            "procedimiento, un proceso o una secuencia de acciones, descomponlos en "
            "pasos breves (uno por acción), en orden. Devuelve id y lista de pasos. "
            "Un bloque no puede estar a la vez en parrafos_simplificados y aquí."
        )
    if o.glosario:
        lineas.append(
            "- glosario: elige entre 3 y 10 términos del documento difíciles para el "
            "nivel objetivo y defínelos con una frase sencilla cada uno."
        )
    if o.resumen:
        lineas.append(
            "- resumen: para cada apartado con (titulo), de 2 a 4 ideas clave en "
            "lenguaje sencillo. Usa como 'apartado' el texto del título."
        )
    if o.preguntas:
        lineas.append(
            f"- preguntas: {o.n_preguntas} preguntas de comprensión sobre el "
            "contenido, ordenadas de más fácil a más difícil, que se puedan "
            "responder leyendo el documento."
        )
    return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Llamada a la API
# --------------------------------------------------------------------------- #

def adaptar_contenido(
    bloques: list[Bloque],
    opciones: OpcionesIA,
    api_key: str | None = None,
    registrar: Callable[[str], None] = lambda mensaje: None,
) -> dict:
    """Envía los bloques a Claude y devuelve un dict con las claves del esquema
    (`parrafos_simplificados`, `parrafos_en_pasos`, `glosario`, `resumen`,
    `preguntas`) más `_uso` con el recuento de tokens."""

    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Falta la librería 'anthropic'. Instálala con: pip install anthropic"
        ) from exc

    clave = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not clave:
        raise RuntimeError(
            "No hay clave de API de Anthropic. Introdúcela en la ventana o define "
            "la variable de entorno ANTHROPIC_API_KEY."
        )

    if not opciones.alguna():
        return {
            "parrafos_simplificados": [],
            "parrafos_en_pasos": [],
            "glosario": [],
            "resumen": [],
            "preguntas": [],
            "_uso": {"entrada": 0, "salida": 0},
        }

    cliente = anthropic.Anthropic(api_key=clave)

    registrar("Enviando el texto a Claude para adaptarlo…")
    try:
        respuesta = cliente.messages.create(
            model=opciones.modelo,
            max_tokens=16000,
            system=_SISTEMA,
            messages=[{"role": "user", "content": _mensaje_usuario(bloques, opciones)}],
            output_config={"format": _esquema()},
        )
    except anthropic.AuthenticationError as exc:
        raise RuntimeError("La clave de API no es válida.") from exc
    except anthropic.PermissionDeniedError as exc:
        raise RuntimeError("La clave de API no tiene permisos para este modelo.") from exc
    except anthropic.NotFoundError as exc:
        raise RuntimeError(f"El modelo «{opciones.modelo}» no está disponible.") from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError(
            "La API está limitando las peticiones. Espera un momento y prueba otra vez."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError("No se pudo conectar con la API. Revisa tu conexión.") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(f"Error de la API ({exc.status_code}): {exc.message}") from exc

    if respuesta.stop_reason == "refusal":
        raise RuntimeError("Claude ha rechazado adaptar este documento.")

    texto = next((b.text for b in respuesta.content if b.type == "text"), "")
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise RuntimeError("No se pudo interpretar la respuesta de la IA.") from exc

    for clave_lista in (
        "parrafos_simplificados",
        "parrafos_en_pasos",
        "glosario",
        "resumen",
        "preguntas",
    ):
        datos.setdefault(clave_lista, [])

    datos["_uso"] = {
        "entrada": respuesta.usage.input_tokens,
        "salida": respuesta.usage.output_tokens,
    }
    registrar(
        f"Respuesta recibida ({datos['_uso']['entrada']} tokens de entrada, "
        f"{datos['_uso']['salida']} de salida)."
    )
    return datos
