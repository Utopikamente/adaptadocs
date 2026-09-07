"""Genera con IA el borrador completo de una ACIS a partir de la programación
didáctica de la materia y el nivel de competencia curricular del alumno.

Envía a la API de Anthropic: las competencias específicas y criterios de la
programación, los saberes básicos, los instrumentos, las unidades didácticas,
el nivel objetivo, el perfil de accesibilidad (necesidades funcionales NO
clínicas) y el currículo oficial de referencia (ESO y, si baja a Primaria,
Primaria). Devuelve, en borrador para el equipo docente:

- las competencias específicas reformuladas a ese nivel (sin eliminar ninguna),
- sus criterios de evaluación al nivel objetivo (con referencia y, si baja a
  Primaria, área y ciclo),
- los contenidos por bloque a ese nivel,
- la metodología (apoyos, agrupamientos, temporalización) según el perfil,
- instrumentos de evaluación accesibles y criterios de calificación,
- cada unidad de la programación con su adaptación.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable

from .acis import MateriaACIS, cargar_textos
from .programacion import Programacion


@dataclass
class OpcionesAdaptacionCurricular:
    nivel_objetivo: str = ""          # p. ej. "2.º ESO" o "Tercer ciclo de Primaria (6.º)"
    necesidades: list[str] = None     # necesidades funcionales NO clínicas (textos ya resueltos)
    barreras: str = ""                # texto libre adicional; opcional
    referencia_curriculo: str = ""    # texto del currículo oficial (ESO / Primaria)
    modelo: str = "claude-opus-5"

    def __post_init__(self) -> None:
        if self.necesidades is None:
            self.necesidades = []


# --------------------------------------------------------------------------- #
# Perfil de accesibilidad (necesidades funcionales, no clínicas)
# --------------------------------------------------------------------------- #

def _perfil() -> dict:
    return cargar_textos().get("perfil_accesibilidad", {})


def grupos_necesidades() -> dict[str, list[tuple[str, str]]]:
    perfil = _perfil()
    textos = perfil.get("necesidades", {})
    return {grupo: [(c, textos[c]) for c in claves if c in textos]
            for grupo, claves in perfil.get("grupos", {}).items()}


def categorias_necesidades() -> list[str]:
    return list(_perfil().get("categorias", {}))


def claves_de_categoria(categoria: str) -> list[str]:
    if not categoria or categoria == "(ninguna)":
        return []
    return list(_perfil().get("categorias", {}).get(categoria, []))


def expandir_categoria(categoria: str) -> list[str]:
    perfil = _perfil()
    textos = perfil.get("necesidades", {})
    return [textos[c] for c in perfil.get("categorias", {}).get(categoria, []) if c in textos]


def textos_de_claves(claves: list[str]) -> list[str]:
    textos = _perfil().get("necesidades", {})
    return [textos[c] for c in claves if c in textos]


# --------------------------------------------------------------------------- #
# Llamada a la API
# --------------------------------------------------------------------------- #

_SISTEMA = (
    "Eres especialista en adaptación curricular individualizada y significativa "
    "(ACIS) en la Comunidad de Madrid. El alumno SIGUE MATRICULADO en su curso "
    "(no cambia de curso ni de etapa): la ACIS hace su programación accesible a "
    "su NIVEL DE COMPETENCIA CURRICULAR real (el de un curso anterior, a veces "
    "de Educación Primaria) y a su perfil de necesidades educativas especiales. "
    "A partir de la programación didáctica de la materia redactas el borrador. "
    "Reglas: "
    "(1) reformulas cada competencia específica al nivel objetivo (más concreta, "
    "frases cortas, lenguaje accesible) SIN eliminar ninguna y manteniendo su "
    "número; "
    "(2) para cada criterio de evaluación de la programación propones su "
    "equivalente al nivel objetivo, con su referencia (p. ej. «1.1.»); si el "
    "nivel es de Primaria, indicas el área y el ciclo; "
    "(3) rebajas los contenidos por bloque a ese nivel; "
    "(4) redactas la metodología: qué cambia respecto a la programación general "
    "(apoyos de PT/AL, agrupamientos, temporalización), teniendo en cuenta el "
    "perfil de accesibilidad; "
    "(5) propones instrumentos de evaluación accesibles y unos criterios de "
    "calificación (pesos por instrumento, no penalizar ortografía/caligrafía/"
    "presentación cuando proceda, corrección por partes, ítems de repaso); "
    "(6) para cada unidad de la programación indicas cómo se adapta (qué léxico "
    "y estructuras esenciales se mantienen a ese nivel) o si procede una unidad "
    "diseñada ex profeso sobre el mismo tema; "
    "(7) NO inventas contenido ajeno al currículo: te apoyas en el currículo "
    "oficial de referencia que se te aporta; "
    "(8) escribes en español y devuelves solo el JSON pedido. Todo es un "
    "BORRADOR que debe revisar y aprobar el equipo docente."
)


def _esquema() -> dict:
    obj = lambda props, req: {  # noqa: E731
        "type": "object", "additionalProperties": False, "required": req, "properties": props,
    }
    criterio = obj({"referencia": {"type": "string"}, "nivel": {"type": "string"},
                    "texto": {"type": "string"}}, ["referencia", "nivel", "texto"])
    return {
        "type": "json_schema",
        "schema": obj(
            {
                "competencias": {
                    "type": "array",
                    "items": obj(
                        {
                            "numero": {"type": "string"},
                            "texto_reformulado": {"type": "string"},
                            "criterios_adaptados": {"type": "array", "items": criterio},
                        },
                        ["numero", "texto_reformulado", "criterios_adaptados"],
                    ),
                },
                "contenidos": {
                    "type": "array",
                    "items": obj(
                        {"bloque": {"type": "string"}, "nivel": {"type": "string"},
                         "items": {"type": "array", "items": {"type": "string"}}},
                        ["bloque", "nivel", "items"],
                    ),
                },
                "metodologia": {"type": "string"},
                "instrumentos": {
                    "type": "array",
                    "items": obj(
                        {"elemento": {"type": "string"}, "propuesta": {"type": "string"},
                         "justificacion": {"type": "string"}},
                        ["elemento", "propuesta", "justificacion"],
                    ),
                },
                "criterios_calificacion": {"type": "string"},
                "unidades": {
                    "type": "array",
                    "items": obj(
                        {"titulo": {"type": "string"}, "adaptacion": {"type": "string"},
                         "periodo": {"type": "string"}},
                        ["titulo", "adaptacion", "periodo"],
                    ),
                },
                "avisos": {"type": "array", "items": {"type": "string"}},
            },
            ["competencias", "contenidos", "metodologia", "instrumentos",
             "criterios_calificacion", "unidades", "avisos"],
        ),
    }

_CLAVES = ("competencias", "contenidos", "metodologia", "instrumentos",
           "criterios_calificacion", "unidades", "avisos")


def _mensaje_usuario(prog: Programacion, opciones: OpcionesAdaptacionCurricular) -> str:
    lineas: list[str] = [
        f"MATERIA: {prog.materia or '(sin nombre)'}",
        f"CURSO EN EL QUE EL ALUMNO SIGUE MATRICULADO: {prog.curso or '(sin indicar)'}",
        f"NIVEL DE COMPETENCIA CURRICULAR REAL DEL ALUMNO (al que se adapta): "
        f"{opciones.nivel_objetivo or '(sin indicar)'}",
        "",
        "COMPETENCIAS ESPECÍFICAS Y CRITERIOS DE EVALUACIÓN DE LA PROGRAMACIÓN:",
    ]
    for c in prog.competencias:
        lineas.append(f"[{c.numero}] {c.texto}")
        for cod, texto in c.criterios:
            lineas.append(f"    {cod} {texto}")
    if not any(c.criterios for c in prog.competencias) and prog.criterios:
        lineas.append("  (criterios de la programación, sin agrupar por competencia):")
        for cod, texto in prog.criterios:
            lineas.append(f"    {cod} {texto}")

    lineas += ["", "SABERES BÁSICOS / CONTENIDOS POR BLOQUE:"]
    for bloque, items in (prog.saberes_basicos or {}).items():
        lineas.append(f"  {bloque}")
        for it in items:
            lineas.append(f"    - {it}")
    if not prog.saberes_basicos and prog.contenidos_texto:
        lineas.append(prog.contenidos_texto)

    if prog.instrumentos or prog.instrumentos_texto:
        lineas += ["", "INSTRUMENTOS DE EVALUACIÓN / CRITERIOS DE CALIFICACIÓN ACTUALES:"]
        for elemento, instrumento in prog.instrumentos:
            lineas.append(f"  - {elemento}: {instrumento}")
        if prog.instrumentos_texto:
            lineas.append(prog.instrumentos_texto)

    if prog.unidades:
        lineas += ["", "UNIDADES DIDÁCTICAS DE LA PROGRAMACIÓN (adáptalas una a una, "
                   "manteniendo el tema):"]
        for titulo, periodo in prog.unidades:
            lineas.append(f"  - {titulo}" + (f"  [{periodo}]" if periodo else ""))

    if opciones.necesidades:
        lineas += ["", "PERFIL DE ACCESIBILIDAD DEL ALUMNO (necesidades funcionales; "
                   "tenlas en cuenta al rebajar criterios y contenidos y, sobre todo, "
                   "en la metodología y los instrumentos):"]
        for n in opciones.necesidades:
            lineas.append(f"  - {n}")
    if opciones.barreras.strip():
        lineas += ["", f"OTRAS INDICACIONES DEL DOCENTE: {opciones.barreras.strip()}"]

    if opciones.referencia_curriculo.strip():
        lineas += ["", "CURRÍCULO OFICIAL DE REFERENCIA (úsalo para no inventar; el "
                   "formato a dos columnas del BOCM es normal):",
                   opciones.referencia_curriculo.strip()]

    lineas += ["", "Devuelve el JSON con todas las claves: competencias "
               "(numero, texto_reformulado, criterios_adaptados[referencia, nivel, texto]), "
               "contenidos (bloque, nivel, items), metodologia, instrumentos "
               "(elemento, propuesta, justificacion), criterios_calificacion, "
               "unidades (titulo, adaptacion, periodo) y avisos."]
    return "\n".join(lineas)


def adaptar_programacion(
    prog: Programacion,
    opciones: OpcionesAdaptacionCurricular,
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
            "No hay clave de API de Anthropic. Guárdala en la pestaña «Contenido "
            "con IA» o define la variable de entorno ANTHROPIC_API_KEY."
        )
    if not (prog.competencias or prog.criterios):
        raise RuntimeError(
            "No se han encontrado competencias ni criterios en la programación de la materia."
        )

    cliente = anthropic.Anthropic(api_key=clave)
    registrar("Enviando la programación a Claude para generar el borrador de ACIS…")
    try:
        respuesta = cliente.messages.create(
            model=opciones.modelo,
            max_tokens=20000,
            system=_SISTEMA,
            messages=[{"role": "user", "content": _mensaje_usuario(prog, opciones)}],
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

    for k in _CLAVES:
        datos.setdefault(k, [] if k not in ("metodologia", "criterios_calificacion") else "")
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

def _texto_competencias(resultado: dict) -> str:
    comps = resultado.get("competencias", [])
    if not comps:
        return ""
    lineas = ["Competencias específicas reformuladas al nivel objetivo (se mantienen "
              f"las {len(comps)}):"]
    for c in comps:
        num = str(c.get("numero", "")).strip()
        txt = str(c.get("texto_reformulado", "")).strip()
        lineas.append(f"{num}. {txt}" if num else txt)
    return "\n".join(lineas)


def _texto_criterios(resultado: dict) -> str:
    bloques: list[str] = []
    for comp in resultado.get("competencias", []):
        num = str(comp.get("numero", "")).strip()
        titulo = str(comp.get("texto_reformulado", "")).strip()
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
        lineas = [cab] + [f"  − {str(it).strip()}"
                          for it in cont.get("items", []) if str(it).strip()]
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
            lineas.append(f"− {linea}")
    texto = "\n".join(lineas)
    calif = str(resultado.get("criterios_calificacion", "")).strip()
    if calif:
        texto = (texto + "\n\n" if texto else "") + "CRITERIOS DE CALIFICACIÓN:\n" + calif
    return texto


def _texto_unidades(resultado: dict) -> str:
    lineas = []
    for u in resultado.get("unidades", []):
        titulo = str(u.get("titulo", "")).strip()
        adap = str(u.get("adaptacion", "")).strip()
        lineas.append(f"− {titulo}: {adap}" if titulo else f"− {adap}")
    return "\n".join(lineas)


def resultado_a_materia(
    prog: Programacion,
    resultado: dict,
    base: MateriaACIS | None = None,
) -> MateriaACIS:
    """Convierte la respuesta de la IA en una `MateriaACIS` lista para
    `core.acis.generar_acis`. `base` aporta materia, profesor, departamento y la
    casilla `acs_determinada` (que decide una persona)."""
    materia = base or MateriaACIS(materia=prog.materia)
    materia.competencias = _texto_competencias(resultado)
    materia.criterios_evaluacion = _texto_criterios(resultado)
    materia.contenidos = _texto_contenidos(resultado)
    if str(resultado.get("metodologia", "")).strip():
        materia.metodologia = str(resultado["metodologia"]).strip()
    materia.instrumentos = _texto_instrumentos(resultado)
    if resultado.get("unidades"):
        materia.unidades = _texto_unidades(resultado)
        materia.secuenciacion = [
            (str(u.get("titulo", "")).strip(), str(u.get("periodo", "")).strip())
            for u in resultado["unidades"] if str(u.get("titulo", "")).strip()
        ]
    return materia
