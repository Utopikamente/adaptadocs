"""Reconstruye `core/curriculo_eso.json` a partir del Anexo II del Decreto
65/2022 (currículo de la ESO, Comunidad de Madrid) con una extracción sin OCR
y sin heurística de reflujo de columnas — sustituye al método anterior
(`extraer_curriculo_eso.py`, basado en `pdftotext -layout`), que perdía
palabras en los saltos de página.

El PDF del BOCM es «born-digital» (lleva su texto incrustado, no es un
escaneado), así que en vez de `pdftotext -layout` (que reordena mal las dos
columnas y pierde palabras en los saltos de página) se extrae con PyMuPDF,
que respeta el orden real del texto. Dos pasos — primero el .txt:

    pip install pymupdf   # solo para esta herramienta, no es dependencia de la app
    python -c "import pymupdf; open('normativa12.txt','w',encoding='utf-8').write(chr(10).join(p.get_text('text') for p in pymupdf.open('normativa (12).pdf')))"

Y luego este script sobre ese .txt:

    python herramientas/actualizar_curriculo_eso.py normativa12.txt core/curriculo_eso.json

Esquema de salida (una entrada por materia, 21 materias):
    {
      "fuente": "...", "nota": "...", "anomalias_del_decreto": {...},
      "materias": {
        "BIOLOGÍA Y GEOLOGÍA": {
          "introduccion": "...",                 # prosa del anexo, tal cual
          "competencias_especificas": "CE1. ... Descriptores: ...\n\nCE2. ...",
          "cursos": {"1": "CRITERIOS DE EVALUACIÓN (1.º ESO)\n...\n\nSABERES BÁSICOS (1.º ESO)\n..."}
        }, ...
      }
    }

"Educación en Valores Cívicos y Éticos" es un caso especial: el Decreto
65/2022 no desarrolla currículo propio para ella y remite al Real Decreto
217/2022 (BOE). Su contenido no sale de este PDF sino de
`herramientas/valores_civicos_rd217.json` (extraído del PDF consolidado del
BOE con el mismo método sin OCR) — ver `_cargar_valores()`.

Las erratas del propio decreto (numeraciones que no casan, p. ej. Biología y
Geología numerando dos competencias como «5», o Matemáticas imprimiendo un
criterio bajo una competencia distinta a la de su propio número) se señalan
en `anomalias_del_decreto` en vez de corregirse en silencio: mejor que el
docente lo sepa que dar por buena una «corrección» que no está en el BOCM.

Compatibilidad: `core/acis_orientaciones.py` (`_texto_eso`) sabe leer tanto
este esquema (dict con introduccion/competencias_especificas/cursos) como el
antiguo (una cadena de texto por materia), así que un JSON viejo sigue
funcionando si por lo que sea no se regenera.
"""
from __future__ import annotations

import json
import os
import re
import sys

FURN = re.compile(
    r'^\s*\d{1,3}\s*$'
    r'|^\s*BOCM\b'
    r'|BOLET[IÍ]N OFICIAL'
    r'|^\s*B\.O\.C\.M'
    r'|MARTES \d+ DE \w+ DE 20\d\d|VIERNES \d+ DE \w+ DE 20\d\d|LUNES \d+ DE \w+ DE 20\d\d'
    r'|^\s*N[uú]m\.\s*\d+\s*$'
    r'|^\s*P[aá]g\.\s*\d+'
    r'|^\s*BOCM-\d+'
)

MATERIAS = [
    "BIOLOGÍA Y GEOLOGÍA", "CIENCIAS DE LA COMPUTACIÓN", "CULTURA CLÁSICA", "DIGITALIZACIÓN",
    "ECONOMÍA Y EMPRENDIMIENTO", "EDUCACIÓN FÍSICA", "EDUCACIÓN PLÁSTICA, VISUAL Y AUDIOVISUAL",
    "EDUCACIÓN EN VALORES CÍVICOS Y ÉTICOS", "EXPRESIÓN ARTÍSTICA", "FILOSOFÍA", "FÍSICA Y QUÍMICA",
    "FORMACIÓN Y ORIENTACIÓN PERSONAL Y PROFESIONAL", "GEOGRAFÍA E HISTORIA", "LATÍN",
    "LENGUA CASTELLANA Y LITERATURA", "LENGUA EXTRANJERA", "MATEMÁTICAS", "MATEMÁTICAS A", "MATEMÁTICAS B",
    "MÚSICA", "SEGUNDA LENGUA EXTRANJERA", "TECNOLOGÍA Y DIGITALIZACIÓN", "TECNOLOGÍA",
]
# materias que solo delimitan el final de la sección anterior (no son ESO: FP básica)
STOP = ["CIENCIAS APLICADAS", "COMUNICACIÓN Y CIENCIAS SOCIALES"]

CE_HEAD = re.compile(r'^\s*Competencias?\s+[Ee]spec[ií]ficas?\.?\s*$')
CE_ITEM = re.compile(r'^\s*(\d{1,2})\.(?!\d)\s*(.*)$')
CE_LINK = re.compile(r'se conecta con los siguientes descriptores')
CC_LIST = re.compile(r':\s*((?:CCL|CP|STEM|CD|CPSAA|CC|CE|CCEC)[\d\.]+.*)$', re.I)
COURSE = re.compile(r'^\s*([1-4])\s*º\s*ESO\.?\s*$')
CRIT_HEAD = re.compile(r'^\s*Criterios de evaluaci[oó]n\.?\s*$')
CE_REF = re.compile(r'^\s*Competencia espec[ií]fica\s+(\d{1,2})\.?\s*$')
CRIT_IT = re.compile(r'^\s*(\d{1,2})\.(\d{1,2})\.?\s+(\S.*)$')
SAB_HEAD = re.compile(r'^\s*(Contenidos|Saberes b[aá]sicos)\.?\s*$')
BLOQUE = re.compile(r'^\s*([A-Z])\.\s+([A-ZÁÉÍÓÚ¿].*)$')
B_MAIN = re.compile(r'^\s*[–−\-]\s+(\S.*)$')
B_SUB = re.compile(r'^\s*[•·]\s*(.*)$')
LANG_HEAD = re.compile(r'^\s*(ALEM[ÁA]N|FRANC[ÉE]S|INGL[ÉE]S|ITALIANO|PORTUGU[ÉE]S)\.?\s*$')

NOM_CURSO = {"1": "1.º ESO", "2": "2.º ESO", "3": "3.º ESO", "4": "4.º ESO", "0": "curso único"}


def nt(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def cargar_lineas(path_pdf_txt: str) -> list[str]:
    raw = open(path_pdf_txt, encoding="utf-8").read().split("\n")
    i = 0
    for i, l in enumerate(raw):
        if l.strip() == "ANEXO II":
            break
    return [l.rstrip() for l in raw[i:] if not FURN.search(l)]


def es_materia(l: str) -> bool:
    return l.strip().rstrip(".") in (MATERIAS + STOP)


def es_marcador(l: str) -> bool:
    return (es_materia(l) or COURSE.match(l) or CE_ITEM.match(l) or CE_REF.match(l) or CRIT_HEAD.match(l)
            or CRIT_IT.match(l) or SAB_HEAD.match(l) or CE_HEAD.match(l) or BLOQUE.match(l)
            or B_MAIN.match(l) or B_SUB.match(l) or LANG_HEAD.match(l))


def unir_hasta_marcador(lineas, i, n):
    buf = []
    while i < n:
        l = lineas[i]
        if not l.strip():
            j = i + 1
            while j < n and not lineas[j].strip():
                j += 1
            if j >= n or es_marcador(lineas[j]) or B_MAIN.match(lineas[j]) or B_SUB.match(lineas[j]):
                break
            i = j
            continue
        if es_marcador(l) or B_MAIN.match(l) or B_SUB.match(l):
            break
        buf.append(l.strip())
        i += 1
    return buf, i


def parsear(lineas: list[str]) -> dict:
    out: dict = {}
    cur = None
    i, n = 0, len(lineas)
    while i < n:
        l = lineas[i]
        if es_materia(l):
            cur = l.strip().rstrip(".")
            if cur in STOP:
                i += 1
                continue
            head = " ".join(x.strip() for x in lineas[i + 1:i + 10])
            out.setdefault(cur, {"ce": [], "cursos": {}, "anomalias": [],
                                 "remite": bool(re.search(r"se recogen en el Real Decreto", head))})
            j, para, paras = i + 1, "", []
            while j < n:
                s = lineas[j].strip()
                if CE_HEAD.match(lineas[j]) or CRIT_HEAD.match(lineas[j]) or SAB_HEAD.match(lineas[j]) \
                        or COURSE.match(lineas[j]) or es_materia(lineas[j]):
                    break
                if s:
                    para = (para + " " + s).strip()
                    if s.endswith((".", ".)", ".»", "…")) and len(para) > 300:
                        paras.append(para)
                        para = ""
                j += 1
            if para:
                paras.append(para)
            out[cur]["intro"] = "\n\n".join(nt(p) for p in paras).strip()
            i += 1
            continue
        if cur is None or cur in STOP:
            i += 1
            continue
        D = out[cur]

        if CE_HEAD.match(l):
            i += 1
            while i < n and not COURSE.match(lineas[i]) and not es_materia(lineas[i]):
                m = CE_ITEM.match(lineas[i])
                if m and int(m.group(1)) == len(D["ce"]) + 1:
                    num = int(m.group(1))
                    txt = m.group(2).strip()
                    i += 1
                    while i < n and not es_marcador(lineas[i]) and not CE_LINK.search(lineas[i]):
                        s = lineas[i].strip()
                        if not s:
                            if txt.rstrip().endswith((".", ".»", "»", "…")):
                                break
                            i += 1
                            continue
                        txt += (" " if txt else "") + s
                        i += 1
                        if txt.rstrip().endswith((".", ".»", "»", "…")):
                            break
                    cc = ""
                    while i < n and not COURSE.match(lineas[i]) and not es_materia(lineas[i]):
                        if CE_LINK.search(lineas[i]):
                            blob, j = lineas[i].strip(), i + 1
                            while j < n and lineas[j].strip() and not CE_ITEM.match(lineas[j]) and not COURSE.match(lineas[j]):
                                blob += " " + lineas[j].strip()
                                j += 1
                                if CC_LIST.search(blob):
                                    break
                            mm = CC_LIST.search(blob)
                            cc = nt(mm.group(1)).rstrip(" .") if mm else ""
                            cc = re.sub(r'\.\s*(?=[A-Z])', ', ', cc)
                            cc = re.sub(r'(\d)\s+(?=[A-Z])', r'\1, ', cc)
                            i = j
                            break
                        nx = CE_ITEM.match(lineas[i])
                        if nx and int(nx.group(1)) == num + 1:
                            break
                        if CRIT_HEAD.match(lineas[i]) or CE_REF.match(lineas[i]):
                            break
                        i += 1
                    D["ce"].append({"id": "CE%d" % num, "texto": nt(txt), "cc": cc})
                else:
                    if CRIT_HEAD.match(lineas[i]) or CE_REF.match(lineas[i]):
                        break
                    i += 1
            continue

        cm = COURSE.match(l)
        abrir = False
        if cm:
            ck, i, abrir = cm.group(1), i + 1, True
        elif (CRIT_HEAD.match(l) or SAB_HEAD.match(l)) and not D["cursos"]:
            ck, abrir = "0", True
        if abrir:
            C = D["cursos"].setdefault(ck, {"criterios": [], "saberes": []})
            modo, blk, ceref = None, None, None
            while i < n and not COURSE.match(lineas[i]) and not es_materia(lineas[i]):
                x = lineas[i]
                if not x.strip():
                    i += 1
                    continue
                if CRIT_HEAD.match(x):
                    modo, ceref, i = "c", None, i + 1
                    continue
                if SAB_HEAD.match(x):
                    modo, blk, i = "s", None, i + 1
                    continue
                r = CE_REF.match(x)
                if r:
                    ceref, i = int(r.group(1)), i + 1
                    continue
                if modo == "c":
                    ci = CRIT_IT.match(x)
                    if ci:
                        pref = int(ci.group(1))
                        rest, i = unir_hasta_marcador(lineas, i + 1, n)
                        cetxt = ci.group(3) + (" " + " ".join(rest) if rest else "")
                        ce_id = "CE%d" % (ceref if ceref else pref)
                        cid = "%s.%s" % (ci.group(1), ci.group(2))
                        if ceref and ceref != pref:
                            D["anomalias"].append(
                                'curso %s: el criterio impreso como "%s" figura bajo "Competencia específica %d"'
                                % (ck, cid, ceref))
                        C["criterios"].append({"ce": ce_id, "id": cid, "texto": nt(cetxt)})
                        continue
                    i += 1
                    continue
                if modo == "s":
                    if LANG_HEAD.match(x):
                        blk, i = None, i + 1  # anexo por idioma: no pertenece al bloque anterior
                        continue
                    b = BLOQUE.match(x)
                    if b:
                        blk = {"b": b.group(1), "t": nt(b.group(2)).rstrip("."), "items": []}
                        C["saberes"].append(blk)
                        i += 1
                        continue
                    bm, bs = B_MAIN.match(x), B_SUB.match(x)
                    if (bm or bs) and blk is not None:
                        head, i = (bm.group(1) if bm else bs.group(1)), i + 1
                        rest, i = unir_hasta_marcador(lineas, i, n)
                        blk["items"].append(("· " if bs else "") + nt(head + (" " + " ".join(rest) if rest else "")))
                        continue
                    i += 1
                    continue
                i += 1
            continue
        i += 1
    return out


def texto_ce(ce_list: list[dict]) -> str:
    partes = []
    for c in ce_list:
        t = "%s. %s" % (c["id"], c["texto"])
        if c.get("cc"):
            t += " Descriptores del perfil de salida: %s." % c["cc"]
        partes.append(t)
    return "\n\n".join(partes)


def texto_curso(curso_key: str, cursodata: dict) -> str:
    nom = NOM_CURSO.get(curso_key, curso_key)
    out = ["CRITERIOS DE EVALUACIÓN (%s)" % nom, ""]
    por_ce: dict = {}
    for x in cursodata.get("criterios", []):
        por_ce.setdefault(x["ce"], []).append(x)
    for ce, items in por_ce.items():
        out.append(ce)
        out.extend("%s %s" % (it["id"], it["texto"]) for it in items)
        out.append("")
    out.append("SABERES BÁSICOS (%s)" % nom)
    out.append("")
    for b in cursodata.get("saberes", []):
        out.append("%s. %s" % (b["b"], b["t"]))
        out.extend(("  " if it.startswith("·") else "- ") + it for it in b.get("items", []))
        out.append("")
    return "\n".join(out).strip()


# El Decreto 65/2022 de Madrid no desarrolla currículo propio para "Educación
# en Valores Cívicos y Éticos": remite al Real Decreto 217/2022 (BOE), que sí
# lo define en su Anexo II, y solo añade un saber al bloque B (la Constitución
# de 1978). Como esta materia no viene del PDF del Decreto 65/2022 que procesa
# este script, sus datos (extraídos del PDF consolidado del BOE con el mismo
# método sin OCR) viven aparte, en herramientas/valores_civicos_rd217.json.
_VALORES_JSON = os.path.join(os.path.dirname(__file__), "valores_civicos_rd217.json")


def _cargar_valores() -> dict:
    with open(_VALORES_JSON, encoding="utf-8") as f:
        return json.load(f)


# El Decreto 65/2022 numera como «5» dos competencias específicas distintas de
# Biología y Geología (medio ambiente/salud, y paisaje) y, en 1.º ESO, imprime
# los criterios de la segunda bajo «5.1-5.3» en vez de «6.1-6.3». Es una
# errata de numeración del propio decreto (no de esta herramienta); se separa
# aquí para que competencias y criterios casen, documentando el motivo.
_BYG_CE5_TEXTO = (
    "Analizar los efectos de determinadas acciones sobre el medio ambiente y la salud, "
    "basándose en los fundamentos de las ciencias biológicas y de la Tierra, para promover "
    "y adoptar hábitos que eviten o minimicen los impactos medioambientales negativos, sean "
    "compatibles con un desarrollo sostenible y permitan mantener y mejorar la salud."
)
_BYG_CE5_CC = "STEM2, STEM5, CD4, CPSAA1, CPSAA2, CC4, CE1, CC3"


def _corregir_biologia(datos: dict) -> None:
    byg = datos.get("BIOLOGÍA Y GEOLOGÍA")
    if not byg or len(byg["ce"]) != 5:
        return
    byg["ce"].append({"id": "CE6", "texto": byg["ce"][4]["texto"], "cc": byg["ce"][4]["cc"]})
    byg["ce"][4] = {"id": "CE5", "texto": _BYG_CE5_TEXTO, "cc": _BYG_CE5_CC}
    byg["anomalias"].insert(0, 'El Decreto 65/2022 numera como "5" dos competencias específicas distintas; '
                                'aquí figuran como CE5 (medio ambiente y salud) y CE6 (paisaje).')
    vistos = 0
    for cr in byg["cursos"].get("1", {}).get("criterios", []):
        if cr["ce"] == "CE5":
            vistos += 1
            if vistos > 3:
                cr["ce"] = "CE6"


def construir_json(datos: dict) -> dict:
    _corregir_biologia(datos)
    materias_out: dict = {}
    for nombre in [m for m in MATERIAS if m not in ("MATEMÁTICAS A", "MATEMÁTICAS B")]:
        if nombre == "EDUCACIÓN EN VALORES CÍVICOS Y ÉTICOS":
            v = _cargar_valores()
            materias_out[nombre] = {
                "introduccion": v["intro"],
                "competencias_especificas": texto_ce(v["ce"]),
                "cursos": {ck: texto_curso(ck, cd) for ck, cd in v["cursos"].items()},
            }
            continue
        M = datos.get(nombre)
        entrada = {"introduccion": M.get("intro", "") if M else "",
                   "competencias_especificas": texto_ce(M.get("ce", [])) if M else "",
                   "cursos": {ck: texto_curso(ck, cd) for ck, cd in (M or {}).get("cursos", {}).items()}}
        if nombre == "MATEMÁTICAS":
            for variante in ("MATEMÁTICAS A", "MATEMÁTICAS B"):
                V = datos.get(variante)
                if V and V.get("cursos", {}).get("4"):
                    extra = texto_curso("4", V["cursos"]["4"])
                    cab = ("\n\n---\n%s (4.º ESO; el decreto no repite los enunciados de las competencias "
                           "específicas, son las mismas de Matemáticas):\n" % variante.title())
                    entrada["cursos"]["4"] = entrada["cursos"].get("4", "") + cab + extra
        materias_out[nombre] = entrada

    anomalias = {n: datos[n]["anomalias"] for n in materias_out if datos.get(n) and datos[n].get("anomalias")}
    valores_anomalias = _cargar_valores().get("anomalias")
    if valores_anomalias:
        anomalias["EDUCACIÓN EN VALORES CÍVICOS Y ÉTICOS"] = valores_anomalias
    return {
        "fuente": ("Decreto 65/2022, de 20 de julio — ANEXO II (Currículo de materias de la ESO). Texto "
                   "oficial extraído de la capa de texto del PDF del BOCM (sin OCR, sin heurística de "
                   "reflujo de columnas), reproducido literalmente. Educación en Valores Cívicos y Éticos es "
                   "la excepción: su texto procede del Real Decreto 217/2022 (BOE), ver anomalías."),
        "nota": ("Cada materia trae su introducción, sus competencias específicas con los descriptores del "
                 "perfil de salida y, por curso, los criterios de evaluación y los saberes básicos, en "
                 "texto oficial. Referencia para la adaptación curricular; editable."),
        "anomalias_del_decreto": anomalias,
        "materias": materias_out,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    lineas = cargar_lineas(sys.argv[1])
    datos = parsear(lineas)
    salida = construir_json(datos)
    json.dump(salida, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Escrito %s — %d materias." % (sys.argv[2], len(salida["materias"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
