"""Adaptación de *contenido* con IA (Claude / API de Anthropic).

A diferencia de `transformador.py`, este módulo **sí** envía el texto del
documento a un servicio externo (la API de Anthropic) para reescribirlo y
generar apoyos. Requiere una clave de API.
"""

from __future__ import annotations

import json
import os
import re
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
    dividir_preguntas: bool = False
    nivel: str = NIVEL_POR_DEFECTO
    modelo: str = "claude-opus-5"
    n_preguntas: int = 5

    def alguna(self) -> bool:
        return any(
            (self.simplificar, self.glosario, self.resumen, self.preguntas,
             self.pasos, self.dividir_preguntas)
        )


@dataclass
class Bloque:
    """Un fragmento del documento que se manda a la IA."""

    id: int
    tipo: str  # "titulo" | "parrafo" | "lista"
    texto: str
    # Solo se usa en bloques (titulo): si además es "candidato a resumen"
    # (el docente lo ha marcado como una sección de verdad, no una etiqueta
    # decorativa como "Actividades" repetida en cada ejercicio). Por defecto
    # True para no cambiar el comportamiento donde no se use la selección de
    # niveles (ver `core.transformador.detectar_niveles_titulo`).
    resumen_candidato: bool = True


# --------------------------------------------------------------------------- #
# Cabeceras con datos del alumno: nunca se envían a la IA
# --------------------------------------------------------------------------- #

# Campos habituales de la cabecera de un examen/ficha ("Nombre y apellidos:
# ___ Curso: ___ Fecha: ___"). Los más específicos van antes que sus
# abreviaturas o partes (p. ej. "nombre y apellidos" antes que "nombre") para
# que la alternancia de la regex los reconozca primero.
_CAMPOS_ALUMNO = (
    "nombre y apellidos", "nombre completo", "apellidos", "nombre",
    "alumno/a", "alumna", "alumno", "nia", "dni",
    "fecha de nacimiento", "f. nac.", "curso", "grupo", "fecha",
)
_CAMPO_RX = "|".join(re.escape(c) for c in _CAMPOS_ALUMNO)
# El valor de cada campo puede estar en blanco (subrayado) o ya rellenado
# (p. ej. un nombre real) — por eso acepta cualquier cosa corta que no sea
# otro ":" ni una frase larga, no solo relleno en blanco.
_VALOR_CAMPO_RX = r"[^:\n]{0,40}?"
_CABECERA_ALUMNO_RX = re.compile(
    rf"^(?:\s*(?:{_CAMPO_RX})\s*:\s*{_VALOR_CAMPO_RX}\s*)+$", re.IGNORECASE
)


def es_cabecera_datos_alumno(texto: str) -> bool:
    """True si `texto` es (solo) una línea de cabecera con campos de datos
    identificativos del alumno, p. ej. "Nombre y apellidos: ___ Curso: ___",
    esté en blanco o ya rellena. Estas líneas nunca deben mandarse a la IA:
    ver CLAUDE.md, "nunca se almacenan datos identificativos de alumnos"."""
    return bool(_CABECERA_ALUMNO_RX.fullmatch(texto.strip()))


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
                "preguntas_divididas": {
                    "type": "array",
                    "items": obj(
                        {
                            "id": {"type": "integer"},
                            "subpreguntas": {"type": "array", "items": {"type": "string"}},
                        },
                        ["id", "subpreguntas"],
                    ),
                },
            },
            [
                "parrafos_simplificados",
                "parrafos_en_pasos",
                "glosario",
                "resumen",
                "preguntas",
                "preguntas_divididas",
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
        # Un título que el docente NO ha marcado como sección de verdad (p.
        # ej. una etiqueta decorativa como "Actividades" repetida en cada
        # ejercicio) se etiqueta aparte para que no genere su propio resumen,
        # aunque sigue protegido de la simplificación igual que cualquier título.
        etiqueta = "titulo_secundario" if b.tipo == "titulo" and not b.resumen_candidato else b.tipo
        lineas.append(f"[{b.id}] ({etiqueta}) {b.texto}")
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
            "(parrafo) y (lista). No toques los (titulo) ni los (titulo_secundario). "
            "Devuelve un elemento por bloque que cambies, con su id y el texto nuevo. "
            "Si un bloque ya es suficientemente sencillo, no lo incluyas."
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
    if o.dividir_preguntas:
        lineas.append(
            "- preguntas_divididas: para los bloques (parrafo) que sean una "
            "pregunta (terminan en «?») y pregunten varias cosas a la vez o sean "
            "muy largas, divídelas en varias preguntas más cortas y consecutivas, "
            "en el mismo orden, sin añadir preguntas nuevas ni responderlas. "
            "Devuelve id y la lista de subpreguntas, cada una terminada en «?». "
            "Si una pregunta ya es corta y pregunta una sola cosa, no la incluyas. "
            "Un bloque no puede estar a la vez en parrafos_simplificados, "
            "parrafos_en_pasos y aquí."
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

    # Segunda barrera (la primera es `pipeline._extraer_bloques`, que ya no
    # los incluye): si por lo que sea llega aquí un bloque de cabecera con
    # datos del alumno, se descarta antes de construir el mensaje a la IA.
    bloques = [b for b in bloques if not es_cabecera_datos_alumno(b.texto)]

    if not opciones.alguna():
        return {
            "parrafos_simplificados": [],
            "parrafos_en_pasos": [],
            "glosario": [],
            "resumen": [],
            "preguntas": [],
            "preguntas_divididas": [],
            "_uso": {"entrada": 0, "salida": 0},
        }

    cliente = anthropic.Anthropic(api_key=clave)

    registrar("Enviando el texto a Claude para adaptarlo…")
    try:
        # En modo "streaming" (obligatorio con max_tokens tan alto: la
        # librería exige poder informar del progreso si la respuesta puede
        # tardar más de 10 minutos), no cambia lo que se recibe al final.
        with cliente.messages.stream(
            model=opciones.modelo,
            max_tokens=32000,
            system=_SISTEMA,
            messages=[{"role": "user", "content": _mensaje_usuario(bloques, opciones)}],
            output_config={"format": _esquema()},
        ) as flujo:
            for _ in flujo.text_stream:
                pass
            respuesta = flujo.get_final_message()
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
    if respuesta.stop_reason == "max_tokens":
        raise RuntimeError(
            "La respuesta se ha cortado por ser demasiado larga (el documento tiene mucho texto "
            "para las tareas pedidas). Prueba a desmarcar alguna tarea (p. ej. glosario o "
            "preguntas) o a adaptar el documento por partes más pequeñas."
        )

    texto = next((b.text for b in respuesta.content if b.type == "text"), "")
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "No se pudo interpretar la respuesta de la IA (no era JSON válido). Prueba otra vez; "
            "si se repite, dímelo con el documento para revisarlo."
        ) from exc

    for clave_lista in (
        "parrafos_simplificados",
        "parrafos_en_pasos",
        "glosario",
        "resumen",
        "preguntas",
        "preguntas_divididas",
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
