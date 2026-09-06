"""Adaptación con IA de los elementos curriculares de una programación al
nivel de un curso anterior, para una adaptación curricular significativa
(ACIS).

Envía a la API de Anthropic: las competencias específicas de la programación
con sus criterios de evaluación, los saberes básicos por bloque, los
instrumentos de evaluación, el nivel objetivo y (opcionalmente) las barreras
del alumno descritas en lenguaje no clínico. Devuelve, por competencia, los
criterios de evaluación rebajados a ese nivel; los contenidos a ese nivel; y
propuestas de instrumentos accesibles. Todo es un BORRADOR: lo valida el
equipo docente.

Las competencias específicas NO se tocan (una ACIS no elimina competencias).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable

from .acis import MateriaACIS
from .programacion import Programacion


@dataclass
class OpcionesAdaptacionCurricular:
    nivel_objetivo: str = ""          # p. ej. "2.º ESO" o "6.º de Primaria (tercer ciclo)"
    barreras: str = ""                # descripción NO clínica; opcional
    modelo: str = "claude-opus-5"


_SISTEMA = (
    "Eres especialista en adaptación curricular significativa (ACIS) en la "
    "Comunidad de Madrid, etapa de Educación Secundaria Obligatoria. Tu tarea "
    "es adaptar los criterios de evaluación, los contenidos y los instrumentos "
    "de evaluación de una materia al NIVEL DE COMPETENCIA CURRICULAR de un "
    "curso anterior, de modo que un alumno que trabaja a ese nivel pueda "
    "entender y acceder a esa información. Reglas: "
    "(1) mantienes las competencias específicas tal cual, no eliminas ninguna; "
    "(2) para cada criterio de evaluación de la programación propones su "
    "equivalente rebajado al nivel objetivo, conservando el vínculo con su "
    "competencia y su referencia (p. ej. «1.1.»); si el nivel objetivo es de "
    "Educación Primaria, indicas el área y el ciclo correspondientes; "
    "(3) rebajas también los contenidos y redactas todo con lenguaje claro y "
    "accesible; (4) propones instrumentos de evaluación accesibles para ese "
    "alumno (pruebas orales, más tiempo, formato adaptado, rúbricas sencillas, "
    "productos en vez de exámenes escritos, etc.); (5) no inventas contenido "
    "ajeno al currículo de la materia; (6) escribes en español; (7) devuelves "
    "solo el JSON pedido. Todo lo que produces es una propuesta en borrador "
    "que debe revisar y aprobar el equipo docente."
)


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
                "competencias": {
                    "type": "array",
                    "items": obj(
                        {
                            "numero": {"type": "string"},
                            "criterios_adaptados": {
                                "type": "array",
                                "items": obj(
                                    {
                                        "referencia": {"type": "string"},
                                        "nivel": {"type": "string"},
                                        "texto": {"type": "string"},
                                    },
                                    ["referencia", "nivel", "texto"],
                                ),
                            },
                        },
                        ["numero", "criterios_adaptados"],
                    ),
                },
                "contenidos": {
                    "type": "array",
                    "items": obj(
                        {
                            "bloque": {"type": "string"},
                            "nivel": {"type": "string"},
                            "items": {"type": "array", "items": {"type": "string"}},
                        },
                        ["bloque", "nivel", "items"],
                    ),
                },
                "instrumentos": {
                    "type": "array",
                    "items": obj(
                        {
                            "elemento": {"type": "string"},
                            "propuesta": {"type": "string"},
                            "justificacion": {"type": "string"},
                        },
                        ["elemento", "propuesta", "justificacion"],
                    ),
                },
                "avisos": {"type": "array", "items": {"type": "string"}},
            },
            ["competencias", "contenidos", "instrumentos", "avisos"],
        ),
    }


def _mensaje_usuario(
    prog: Programacion,
    opciones: OpcionesAdaptacionCurricular,
    referencia: Programacion | None,
) -> str:
    lineas: list[str] = [
        f"MATERIA: {prog.materia or '(sin nombre)'}  ·  CURSO DE ORIGEN: {prog.curso or '(sin indicar)'}",
        f"NIVEL DE COMPETENCIA CURRICULAR OBJETIVO DEL ALUMNO: {opciones.nivel_objetivo or '(sin indicar)'}",
        "",
        "COMPETENCIAS ESPECÍFICAS Y CRITERIOS DE EVALUACIÓN DE LA PROGRAMACIÓN "
        "(las competencias se mantienen; adapta sus criterios):",
    ]
    for c in prog.competencias:
        lineas.append(f"[{c.numero}] {c.texto}")
        for cod, texto in c.criterios:
            lineas.append(f"    {cod} {texto}")
    lineas += ["", "SABERES BÁSICOS / CONTENIDOS POR BLOQUE:"]
    for bloque, items in prog.saberes_basicos.items():
        lineas.append(f"  {bloque}")
        for it in items:
            lineas.append(f"    - {it}")
    if prog.instrumentos:
        lineas += ["", "INSTRUMENTOS DE EVALUACIÓN ACTUALES:"]
        for elemento, instrumento in prog.instrumentos:
            lineas.append(f"  - {elemento}: {instrumento}")
    if referencia is not None and referencia.competencias:
        lineas += [
            "",
            f"REFERENCIA DEL NIVEL OBJETIVO (programación de {referencia.curso or 'el curso inferior'}): "
            "úsala para saber qué se espera a ese nivel.",
        ]
        for c in referencia.competencias:
            for cod, texto in c.criterios:
                lineas.append(f"    {cod} {texto}")
    if opciones.barreras.strip():
        lineas += [
            "",
            "BARRERAS DEL ALUMNO (lenguaje no clínico; tenlas en cuenta sobre todo "
            f"para los instrumentos de evaluación): {opciones.barreras.strip()}",
        ]
    lineas += [
        "",
        "Devuelve el JSON: 'competencias' (con 'numero' y 'criterios_adaptados': "
        "referencia, nivel y texto), 'contenidos' (bloque, nivel, items), "
        "'instrumentos' (elemento, propuesta, justificacion) y 'avisos' (texto "
        "libre: dónde has tenido que bajar a Primaria, qué requiere decisión del "
        "equipo docente, etc.).",
    ]
    return "\n".join(lineas)


def adaptar_programacion(
    prog: Programacion,
    opciones: OpcionesAdaptacionCurricular,
    referencia: Programacion | None = None,
    api_key: str | None = None,
    registrar: Callable[[str], None] = lambda mensaje: None,
) -> dict:
    """Llama a la API y devuelve un dict con las claves del esquema más `_uso`."""
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
    if not prog.competencias:
        raise RuntimeError("La programación no tiene competencias/criterios que adaptar.")

    cliente = anthropic.Anthropic(api_key=clave)
    registrar("Enviando la programación a Claude para adaptarla al nivel indicado…")
    try:
        respuesta = cliente.messages.create(
            model=opciones.modelo,
            max_tokens=16000,
            system=_SISTEMA,
            messages=[{"role": "user",
                       "content": _mensaje_usuario(prog, opciones, referencia)}],
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
        raise RuntimeError("Claude ha rechazado adaptar esta programación.")

    texto = next((b.text for b in respuesta.content if b.type == "text"), "")
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise RuntimeError("No se pudo interpretar la respuesta de la IA.") from exc

    for clave_lista in ("competencias", "contenidos", "instrumentos", "avisos"):
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


# --------------------------------------------------------------------------- #
# Volcado del resultado a los campos de una MateriaACIS (sin red, testeable)
# --------------------------------------------------------------------------- #

def _texto_criterios(prog: Programacion, resultado: dict) -> str:
    por_numero = {c.numero: c for c in prog.competencias}
    bloques: list[str] = []
    for comp in resultado.get("competencias", []):
        num = str(comp.get("numero", "")).strip()
        origen = por_numero.get(num)
        titulo = origen.texto if origen else ""
        cabecera = f"Competencia específica {num}".strip()
        if titulo:
            cabecera += f" — {titulo}"
        lineas = [cabecera]
        for cr in comp.get("criterios_adaptados", []):
            ref = str(cr.get("referencia", "")).strip()
            nivel = str(cr.get("nivel", "")).strip()
            txt = str(cr.get("texto", "")).strip()
            prefijo = " ".join(x for x in (ref, f"({nivel})" if nivel else "") if x)
            lineas.append(f"  {prefijo} {txt}".rstrip())
        bloques.append("\n".join(lineas))
    return "\n\n".join(bloques)


def _texto_contenidos(resultado: dict) -> str:
    bloques: list[str] = []
    for cont in resultado.get("contenidos", []):
        bloque = str(cont.get("bloque", "")).strip()
        nivel = str(cont.get("nivel", "")).strip()
        cab = f"{bloque} ({nivel})" if nivel else bloque
        lineas = [cab] + [f"  − {str(it).strip()}" for it in cont.get("items", []) if str(it).strip()]
        bloques.append("\n".join(lineas))
    return "\n\n".join(bloques)


def _texto_instrumentos(resultado: dict) -> str:
    lineas: list[str] = []
    for ins in resultado.get("instrumentos", []):
        elemento = str(ins.get("elemento", "")).strip()
        propuesta = str(ins.get("propuesta", "")).strip()
        just = str(ins.get("justificacion", "")).strip()
        linea = f"{elemento}: {propuesta}" if elemento else propuesta
        if just:
            linea += f" — {just}"
        if linea:
            lineas.append(linea)
    return "\n".join(lineas)


def resultado_a_materia(
    prog: Programacion,
    resultado: dict,
    base: MateriaACIS | None = None,
) -> MateriaACIS:
    """Convierte la respuesta de la IA en una `MateriaACIS` lista para
    `core.acis.generar_acis`. Parte de `base` (donde vienen materia, profesor,
    departamento y la casilla `acs_determinada`, que decide una persona) y
    rellena los tres campos adaptados."""
    materia = base or MateriaACIS(materia=prog.materia)
    materia.criterios_evaluacion = _texto_criterios(prog, resultado)
    materia.contenidos = _texto_contenidos(resultado)
    materia.instrumentos = _texto_instrumentos(resultado)
    return materia
