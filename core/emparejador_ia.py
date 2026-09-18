"""Genera con IA una propuesta adaptada para los criterios y saberes básicos
que `core.emparejador` ha dejado sin equivalente literal en el nivel de
referencia (el decreto no los repite igual en ambos cursos).

A diferencia de `core.acis_ia` (que reformula TODA la programación), aquí
solo se adaptan los huecos puntuales: se le pasa a la IA, como modelo de
estilo y dificultad, los criterios/saberes que SÍ existen literales en esa
misma materia y nivel de referencia (los que ya encontró el emparejador), y
se le pide que adapte únicamente los que faltan, sin inventar una
competencia nueva ni alejarse del tema de cada uno.

Nunca se envían datos del alumno: solo texto curricular (igual que
`core.acis_ia`).
"""

from __future__ import annotations

import json
import os
from typing import Callable

from .acis import MateriaACIS
from .emparejador import (
    CriterioEmparejado,
    SaberEmparejado,
    _normalizar_criterio_id,
    avisos,
    emparejar_criterios,
    emparejar_saberes,
    texto_criterios,
    texto_saberes,
)
from .programacion import Programacion

_SISTEMA = (
    "Eres especialista en currículo LOMLOE de la Comunidad de Madrid (ESO). Se te dan criterios de "
    "evaluación y bloques de saberes básicos de un curso que NO tienen un equivalente literal en un "
    "nivel de referencia inferior (el decreto no los repite igual en ambos cursos). Tu tarea es "
    "proponer, para cada uno, una versión adaptada a ese nivel de referencia, tomando como modelo el "
    "vocabulario, la extensión y la dificultad de los criterios y saberes YA EXISTENTES y literales de "
    "esa misma materia y nivel que se te aportan como ejemplo. No inventas una competencia específica "
    "nueva ni te alejas del tema del elemento de origen que estás adaptando: te ciñes a rebajar su "
    "dificultad al nivel de referencia, igual que hace el propio decreto entre cursos. Escribes en "
    "español y devuelves solo el JSON pedido, con una entrada por cada elemento pendiente que se te da."
)


def _esquema() -> dict:
    return {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["criterios_adaptados", "saberes_adaptados"],
            "properties": {
                "criterios_adaptados": {
                    "type": "array",
                    "items": {
                        "type": "object", "additionalProperties": False,
                        "required": ["numero", "texto"],
                        "properties": {"numero": {"type": "string"}, "texto": {"type": "string"}},
                    },
                },
                "saberes_adaptados": {
                    "type": "array",
                    "items": {
                        "type": "object", "additionalProperties": False,
                        "required": ["titulo", "items"],
                        "properties": {
                            "titulo": {"type": "string"},
                            "items": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        },
    }


def _mensaje_huecos(
    materia: str,
    curso_origen: str,
    curso_referencia: str,
    pendientes_cr: list[CriterioEmparejado],
    pendientes_sa: list[SaberEmparejado],
    anclas_cr: list[CriterioEmparejado],
    anclas_sa: list[SaberEmparejado],
) -> str:
    lineas: list[str] = [
        f"MATERIA: {materia}",
        f"CURSO EN QUE ESTÁ MATRICULADO EL ALUMNO: {curso_origen}",
        f"NIVEL DE REFERENCIA CURRICULAR AL QUE SE ADAPTA: {curso_referencia}",
    ]
    if anclas_cr:
        lineas += ["", "CRITERIOS DE EVALUACIÓN YA EXISTENTES Y LITERALES EN EL NIVEL DE REFERENCIA "
                   "(úsalos como modelo de estilo, vocabulario y dificultad; no los repitas):"]
        for r in anclas_cr:
            lineas.append(f"  [{r.competencia}] {r.numero} {r.texto_referencia}")
    if anclas_sa:
        lineas += ["", "SABERES BÁSICOS YA EXISTENTES Y LITERALES EN EL NIVEL DE REFERENCIA "
                   "(mismo uso, como modelo):"]
        for r in anclas_sa:
            lineas.append(f"  [{r.titulo}] " + "; ".join(r.items_referencia))
    if pendientes_cr:
        lineas += ["", "CRITERIOS DE EVALUACIÓN DEL CURSO DE ORIGEN SIN EQUIVALENTE LITERAL EN EL "
                   "NIVEL DE REFERENCIA (adáptalos tú, uno a uno, sin inventar una competencia nueva "
                   "ni salirte del tema de cada uno):"]
        for r in pendientes_cr:
            lineas.append(f"  [{r.competencia}] {r.numero} {r.texto_origen}")
    if pendientes_sa:
        lineas += ["", "BLOQUES DE SABERES BÁSICOS DEL CURSO DE ORIGEN SIN EQUIVALENTE LITERAL "
                   "(adáptalos tú, sin inventar temas nuevos):"]
        for r in pendientes_sa:
            lineas.append(f"  [{r.titulo}] " + "; ".join(r.items_origen))
    lineas += ["", "Devuelve el JSON con «criterios_adaptados» (numero, texto) y «saberes_adaptados» "
               "(titulo, items), uno por cada elemento pendiente de arriba, en el mismo orden. No "
               "incluyas nada de lo que ya venía como modelo."]
    return "\n".join(lineas)


def adaptar_huecos(
    materia: str,
    curso_origen: str,
    curso_referencia: str,
    pendientes_cr: list[CriterioEmparejado],
    pendientes_sa: list[SaberEmparejado],
    anclas_cr: list[CriterioEmparejado],
    anclas_sa: list[SaberEmparejado],
    api_key: str | None = None,
    modelo: str = "claude-opus-5",
    registrar: Callable[[str], None] = lambda mensaje: None,
) -> dict:
    """Llama a la API y devuelve {"criterios_adaptados": [...], "saberes_adaptados": [...], "_uso": {...}}.
    Si no hay nada pendiente, no llama a la API (devuelve listas vacías)."""
    if not pendientes_cr and not pendientes_sa:
        return {"criterios_adaptados": [], "saberes_adaptados": [], "_uso": {"entrada": 0, "salida": 0}}

    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Falta la librería 'anthropic'. Instálala con: pip install anthropic"
        ) from exc

    clave = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not clave:
        raise RuntimeError(
            "No hay clave de API de Anthropic. Guárdala en la pestaña «Contenido con IA» o define "
            "la variable de entorno ANTHROPIC_API_KEY."
        )

    cliente = anthropic.Anthropic(api_key=clave)
    registrar("Generando propuestas adaptadas para los criterios/saberes sin equivalente literal…")
    mensaje = _mensaje_huecos(materia, curso_origen, curso_referencia,
                               pendientes_cr, pendientes_sa, anclas_cr, anclas_sa)
    try:
        # Streaming (obligatorio con max_tokens tan alto): no cambia lo que
        # se recibe al final, solo cómo se pide.
        with cliente.messages.stream(
            model=modelo,
            max_tokens=32000,
            system=_SISTEMA,
            messages=[{"role": "user", "content": mensaje}],
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
        raise RuntimeError(f"El modelo «{modelo}» no está disponible.") from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError(
            "La API está limitando las peticiones. Espera un momento y prueba otra vez."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError("No se pudo conectar con la API. Revisa tu conexión.") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(f"Error de la API ({exc.status_code}): {exc.message}") from exc

    if respuesta.stop_reason == "refusal":
        raise RuntimeError("Claude ha rechazado adaptar estos elementos.")
    if respuesta.stop_reason == "max_tokens":
        raise RuntimeError(
            "La respuesta se ha cortado por ser demasiado larga (demasiados criterios/saberes "
            "sin equivalente a la vez). Prueba con menos huecos de golpe, o dímelo para revisarlo."
        )

    texto = next((b.text for b in respuesta.content if b.type == "text"), "")
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "No se pudo interpretar la respuesta de la IA (no era JSON válido). Prueba otra vez; "
            "si se repite, dímelo para revisarlo."
        ) from exc

    datos.setdefault("criterios_adaptados", [])
    datos.setdefault("saberes_adaptados", [])
    datos["_uso"] = {
        "entrada": respuesta.usage.input_tokens,
        "salida": respuesta.usage.output_tokens,
    }
    registrar(
        f"Propuestas recibidas ({datos['_uso']['entrada']} tokens de entrada, "
        f"{datos['_uso']['salida']} de salida)."
    )
    return datos


def aplicar_adaptacion(
    curso_origen: str,
    curso_referencia: str,
    pendientes_cr: list[CriterioEmparejado],
    pendientes_sa: list[SaberEmparejado],
    resultado: dict,
) -> None:
    """Vuelca `resultado` (la respuesta de `adaptar_huecos`, o una simulada
    en las pruebas) sobre los propios objetos `pendientes_cr`/`pendientes_sa`
    -los muta in-place-: si la IA propone algo para un elemento, se marca
    `adaptado=True` y se rellena con la propuesta, dejando claro en la
    referencia que NO es cita literal del decreto. Si la IA no propone nada
    para alguno, se queda igual (pendiente), no se inventa nada aquí."""
    # La IA puede devolver el número sin el punto final ("2.2" en vez de
    # "2.2.", que es como lo guarda `core.programacion`): se normaliza antes
    # de comparar, igual que hace `core.emparejador` con la tabla del
    # currículo, para no perder en silencio una propuesta ya generada.
    por_numero = {
        _normalizar_criterio_id(c.get("numero", "")): c for c in resultado.get("criterios_adaptados", [])
    }
    for r in pendientes_cr:
        propuesta = por_numero.get(_normalizar_criterio_id(r.numero))
        texto = str(propuesta.get("texto", "")).strip() if propuesta else ""
        if texto:
            r.adaptado = True
            r.texto_referencia = texto
            r.referencia = (
                f"Propuesta adaptada a partir del criterio {r.numero} de {curso_origen}; no existe "
                f"un criterio equivalente en el Decreto 65/2022 para {curso_referencia}."
            )

    # Mismo motivo que arriba: comparar sin espacios/punto final ni
    # mayúsculas de más, no confiar en que la IA repita el título exacto.
    def _normalizar_titulo(t: str) -> str:
        return (t or "").strip().rstrip(".").casefold()

    por_titulo = {_normalizar_titulo(s.get("titulo", "")): s for s in resultado.get("saberes_adaptados", [])}
    for r in pendientes_sa:
        propuesta = por_titulo.get(_normalizar_titulo(r.titulo))
        items = [str(it).strip() for it in propuesta.get("items", [])] if propuesta else []
        items = [it for it in items if it]
        if items:
            r.adaptado = True
            r.items_referencia = items
            r.referencia = (
                f"Propuesta adaptada a partir del bloque «{r.titulo}» de {curso_origen}; no existe "
                f"un bloque equivalente en el Decreto 65/2022 para {curso_referencia}."
            )


def emparejar_programacion_con_ia(
    materia: str,
    programacion: Programacion,
    curso_referencia: str,
    tabla: dict,
    api_key: str | None = None,
    modelo: str = "claude-opus-5",
    base: MateriaACIS | None = None,
    registrar: Callable[[str], None] = lambda mensaje: None,
) -> MateriaACIS:
    """Como `core.emparejador.emparejar_programacion`, pero además genera con
    IA una propuesta para los huecos sin equivalente literal, en vez de
    dejarlos pendientes. Si no hay ningún hueco, no llama a la API (coste
    cero); si hay huecos y no hay clave de API, se propaga el mismo error
    que ya lanza `adaptar_huecos`."""
    resultado_cr = emparejar_criterios(materia, programacion.competencias, curso_referencia, tabla)
    resultado_sa = emparejar_saberes(materia, programacion.saberes_basicos, curso_referencia, tabla)

    pendientes_cr = [r for r in resultado_cr if not r.encontrado]
    pendientes_sa = [r for r in resultado_sa if not r.encontrado]
    if pendientes_cr or pendientes_sa:
        anclas_cr = [r for r in resultado_cr if r.encontrado]
        anclas_sa = [r for r in resultado_sa if r.encontrado]
        datos = adaptar_huecos(
            materia, programacion.curso, curso_referencia,
            pendientes_cr, pendientes_sa, anclas_cr, anclas_sa,
            api_key=api_key, modelo=modelo, registrar=registrar,
        )
        aplicar_adaptacion(programacion.curso, curso_referencia, pendientes_cr, pendientes_sa, datos)

    m = base or MateriaACIS(materia=materia)
    m.criterios_evaluacion = texto_criterios(resultado_cr)
    m.contenidos = texto_saberes(resultado_sa)
    m.avisos_ia = list(m.avisos_ia) + avisos(resultado_cr, resultado_sa)
    return m
