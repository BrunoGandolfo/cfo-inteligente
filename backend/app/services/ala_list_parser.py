"""
Servicio de parseo y matching para listas ALA (PEP, ONU, OFAC, UE).

Funciones puras: no acceden a BD. Descarga, normalización y verificación
contra listas ya descargadas.
"""

import csv
import hashlib
import io
import logging
import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Constantes
# -----------------------------------------------------------------------------

UMBRAL_SIMILITUD = 0.85
TIMEOUT_SEGUNDOS = 60

URL_PEP = (
    "https://catalogodatos.gub.uy/dataset/bcf06dc6-c41e-4307-b466-8168e7556542/resource"
    "/fdb17214-13a8-4604-acec-b11a1c612957/download/lista-actualizada-de-pep.csv"
)
URL_ONU = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
URL_OFAC = (
    "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML"
)
URL_UE = (
    "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content"
    "?token=dG9rZW4tMjAxNw"
)

# Códigos ISO 3166-1 alpha-2. GAFI "Call for Action" = alto riesgo.
GAFI_ALTO_RIESGO = {"IR", "KP", "MM"}  # Iran, Corea del Norte, Myanmar
# GAFI "Increased monitoring" (grey list). Lista no exhaustiva.
GAFI_GREY_LIST = {
    "SY", "YE", "HT", "PK", "NI", "JM", "TZ", "UG", "VN", "PH",
    "AL", "BB", "BF", "CM", "JO", "NG", "PA", "ZA", "TR", "VE",
}

# Namespace ONU (puede variar según versión del XML)
ONU_NS = {"un": "https://scsanctions.un.org/consolidated/"}


# -----------------------------------------------------------------------------
# 1. Normalización
# -----------------------------------------------------------------------------

def normalizar_texto(texto: Optional[str]) -> str:
    """NFKD + ASCII + upper + strip + espacios. Para comparación de nombres."""
    if not texto:
        return ""
    s = unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("ASCII")
    s = s.upper().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalizar_ci(ci: Optional[str]) -> str:
    """Solo dígitos."""
    if ci is None:
        return ""
    return re.sub(r"\D", "", str(ci))


def similitud_nombres(nombre1: str, nombre2: str) -> float:
    """Jaccard sobre conjuntos de palabras. Devuelve float en [0.0, 1.0]."""
    n1 = set(normalizar_texto(nombre1).split())
    n2 = set(normalizar_texto(nombre2).split())
    if not n1 or not n2:
        return 0.0
    inter = len(n1 & n2)
    union = len(n1 | n2)
    return inter / union if union > 0 else 0.0


def _sha256_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# -----------------------------------------------------------------------------
# 2. Descarga de listas
# -----------------------------------------------------------------------------

def descargar_lista_pep() -> Optional[Dict[str, Any]]:
    """
    Descarga CSV PEP (SENACLAFT). Retorna {registros, hash, total} o None.
    """
    try:
        resp = requests.get(URL_PEP, timeout=TIMEOUT_SEGUNDOS)
        resp.raise_for_status()
        content = resp.content
        h = _sha256_content(content)
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("latin-1")
        reader = csv.DictReader(io.StringIO(text))
        registros = list(reader)
        logger.info("Lista PEP descargada: %d registros, hash=%s", len(registros), h[:16])
        return {"registros": registros, "hash": h, "total": len(registros)}
    except requests.RequestException as e:
        logger.warning("Error descargando lista PEP: %s", e)
        return None
    except Exception as e:
        logger.exception("Error procesando lista PEP: %s", e)
        return None


def descargar_lista_onu() -> Optional[Dict[str, Any]]:
    """
    Descarga XML consolidado ONU. Retorna {individuos, hash, total} o None.
    Prueba con namespace y sin namespace.
    """
    try:
        resp = requests.get(URL_ONU, timeout=TIMEOUT_SEGUNDOS)
        resp.raise_for_status()
        content = resp.content
        h = _sha256_content(content)
        root = ET.fromstring(content)
        # Con namespace
        individuos = root.findall(".//un:INDIVIDUAL", ONU_NS)
        if not individuos:
            individuos = root.findall(".//INDIVIDUAL")
        if not individuos:
            individuos = [
                elem
                for elem in root.iter()
                if elem.tag.endswith("INDIVIDUAL") or elem.tag == "INDIVIDUAL"
            ]
        logger.info("Lista ONU descargada: %d individuos, hash=%s", len(individuos), h[:16])
        return {"individuos": individuos, "hash": h, "total": len(individuos)}
    except requests.RequestException as e:
        logger.warning("Error descargando lista ONU: %s", e)
        return None
    except ET.ParseError as e:
        logger.warning("Error parseando XML ONU: %s", e)
        return None
    except Exception as e:
        logger.exception("Error procesando lista ONU: %s", e)
        return None


def _extraer_nombres_ofac(individuo: ET.Element) -> List[str]:
    """Extrae nombres de un sdnEntry/entidad OFAC (firstName, lastName, etc.)."""
    nombres: List[str] = []
    for tag in ("firstName", "lastName", "lastName2", "firstLastName", "secondLastName"):
        for elem in individuo.iter(tag):
            if elem.text and elem.text.strip():
                nombres.append(elem.text.strip())
    # Sin namespace: tag puede ser {ns}firstName
    if not nombres:
        for elem in individuo.iter():
            if elem.text and elem.text.strip():
                t = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if t in ("firstName", "lastName", "lastName2", "firstLastName", "secondLastName", "wholeName"):
                    nombres.append(elem.text.strip())
    return nombres


def descargar_lista_ofac() -> Optional[Dict[str, Any]]:
    """
    Descarga XML SDN OFAC. Retorna {registros: list of name lists, hash, total} o None.
    Estructura típica: sdnList/sdnEntry con firstName, lastName, etc.
    """
    try:
        resp = requests.get(URL_OFAC, timeout=TIMEOUT_SEGUNDOS)
        resp.raise_for_status()
        content = resp.content
        h = _sha256_content(content)
        root = ET.fromstring(content)
        registros = []
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag in ("sdnEntry", "sdnentry"):
                nombres = _extraer_nombres_ofac(elem)
                if nombres:
                    registros.append(nombres)
        # Alternativa: entries con lastName/firstName a nivel raíz
        if not registros:
            for entry in root.findall(".//*"):
                tag = entry.tag.split("}")[-1] if "}" in entry.tag else entry.tag
                if tag in ("sdnEntry", "sdnentry", "lastName", "firstName"):
                    nombres = _extraer_nombres_ofac(entry) if tag in ("sdnEntry", "sdnentry") else []
                    if not nombres and entry.text:
                        nombres = [entry.text.strip()]
                    if nombres:
                        registros.append(nombres)
        logger.info("Lista OFAC descargada: %d entradas, hash=%s", len(registros), h[:16])
        return {"registros": registros, "hash": h, "total": len(registros)}
    except requests.RequestException as e:
        logger.warning("Error descargando lista OFAC: %s", e)
        return None
    except ET.ParseError as e:
        logger.warning("Error parseando XML OFAC: %s", e)
        return None
    except Exception as e:
        logger.exception("Error procesando lista OFAC: %s", e)
        return None


def _extraer_nombres_ue(elem: ET.Element) -> List[str]:
    """Extrae nombres de un elemento designado UE (firstName, lastName, wholeName, alias)."""
    nombres: List[str] = []
    for e in elem.iter():
        tag = e.tag.split("}")[-1] if "}" in e.tag else e.tag
        if tag in ("firstName", "lastName", "wholeName", "name", "alias", "title"):
            if e.text and e.text.strip():
                nombres.append(e.text.strip())
    return nombres


def descargar_lista_ue() -> Optional[Dict[str, Any]]:
    """
    Descarga XML sanciones UE. Retorna {registros: list of names, hash, total} o None.
    
    El XML de UE tiene estructura:
    <export>
      <sanctionEntity>
        <nameAlias wholeName="..." firstName="..." lastName="..." .../>
        ...
      </sanctionEntity>
      ...
    </export>
    
    Los nombres están en el atributo 'wholeName' de elementos 'nameAlias'.
    """
    try:
        # Timeout de 120s porque el XML de UE es grande (~10MB)
        resp = requests.get(URL_UE, timeout=120)
        resp.raise_for_status()
        content = resp.content
        h = _sha256_content(content)
        root = ET.fromstring(content)
        
        # Extraer wholeName de todos los elementos nameAlias
        nombres_raw: List[str] = []
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "nameAlias":
                whole_name = elem.attrib.get("wholeName", "").strip()
                if whole_name:
                    nombres_raw.append(whole_name)
        
        # Deduplicar por nombre normalizado (preservando el original)
        seen_normalized: set = set()
        registros: List[str] = []
        for nombre in nombres_raw:
            nombre_norm = normalizar_texto(nombre)
            if nombre_norm and nombre_norm not in seen_normalized:
                seen_normalized.add(nombre_norm)
                registros.append(nombre)
        
        logger.info("Lista UE descargada: %d nombres únicos, hash=%s", len(registros), h[:16])
        return {"registros": registros, "hash": h, "total": len(registros)}
    except requests.RequestException as e:
        logger.warning("Error descargando lista UE: %s", e)
        return None
    except ET.ParseError as e:
        logger.warning("Error parseando XML UE: %s", e)
        return None
    except Exception as e:
        logger.exception("Error procesando lista UE: %s", e)
        return None


# -----------------------------------------------------------------------------
# 3. Verificación contra listas (listas ya descargadas)
# -----------------------------------------------------------------------------

def verificar_pep(
    ci: Optional[str],
    nombre: str,
    lista_pep: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verifica persona contra lista PEP ya descargada.
    Retorna: es_pep, match_tipo (CI_EXACTA | NOMBRE_FUZZY | NO_MATCH), similitud,
    mejor_match, cargo, organismo, error (opcional).
    """
    out = {
        "es_pep": False,
        "match_tipo": "NO_MATCH",
        "similitud": 0.0,
        "mejor_match": "",
        "cargo": "",
        "organismo": "",
        "error": None,
    }
    if not lista_pep or "registros" not in lista_pep:
        out["error"] = "Lista PEP no disponible"
        return out
    registros = lista_pep["registros"]
    ci_norm = normalizar_ci(ci)
    nombre_norm = normalizar_texto(nombre)
    # Match por CI exacta
    for reg in registros:
        ci_reg = normalizar_ci(reg.get("CI", ""))
        if ci_reg and ci_reg == ci_norm:
            out["es_pep"] = True
            out["match_tipo"] = "CI_EXACTA"
            out["similitud"] = 1.0
            out["mejor_match"] = (reg.get("NOMBRE") or "")[:200]
            out["cargo"] = reg.get("CARGO") or ""
            out["organismo"] = reg.get("ORGANISMO") or ""
            return out
    # Match por nombre (Jaccard)
    mejor_sim = 0.0
    mejor_reg = None
    for reg in registros:
        nombre_reg = normalizar_texto(reg.get("NOMBRE", ""))
        if not nombre_reg:
            continue
        sim = similitud_nombres(nombre_norm, nombre_reg)
        if sim > mejor_sim:
            mejor_sim = sim
            mejor_reg = reg
    out["similitud"] = mejor_sim
    if mejor_reg:
        out["mejor_match"] = (mejor_reg.get("NOMBRE") or "")[:200]
    if mejor_sim >= UMBRAL_SIMILITUD:
        out["es_pep"] = True
        out["match_tipo"] = "NOMBRE_FUZZY"
        out["cargo"] = (mejor_reg or {}).get("CARGO") or ""
        out["organismo"] = (mejor_reg or {}).get("ORGANISMO") or ""
    return out


def _local_tag(elem: ET.Element) -> str:
    """Tag sin namespace."""
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _verificar_contra_individuos_onu(
    nombre_buscar: str,
    individuos: List[ET.Element],
) -> Dict[str, Any]:
    """Recorre individuos ONU (con/sin ns), incluye alias. Retorna en_lista, similitud, mejor_match, nombres_encontrados."""
    resultado = {
        "en_lista": False,
        "similitud": 0.0,
        "mejor_match": "",
        "nombres_encontrados": [],
        "error": None,
    }
    name_tags = {"FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME", "NAME_ORIGINAL_SCRIPT", "COMMENTS1", "ALIAS_NAME"}
    mejor_sim = 0.0
    for ind in individuos:
        nombres_xml: List[str] = []
        for elem in ind.iter():
            if _local_tag(elem) in name_tags and elem.text and elem.text.strip():
                nombres_xml.append(elem.text.strip())
        for nombre_onu in nombres_xml:
            sim = similitud_nombres(nombre_buscar, nombre_onu)
            if sim > mejor_sim:
                mejor_sim = sim
                resultado["mejor_match"] = nombre_onu[:200]
            if sim >= UMBRAL_SIMILITUD:
                resultado["en_lista"] = True
                if nombre_onu not in resultado["nombres_encontrados"]:
                    resultado["nombres_encontrados"].append(nombre_onu)
    resultado["similitud"] = mejor_sim
    return resultado


def verificar_onu(nombre: str, lista_onu: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica contra lista ONU ya descargada. Incluye alias.
    Retorna: en_lista, similitud, mejor_match, nombres_encontrados, error.
    """
    out = {
        "en_lista": False,
        "similitud": 0.0,
        "mejor_match": "",
        "nombres_encontrados": [],
        "error": None,
    }
    if not lista_onu or "individuos" not in lista_onu:
        out["error"] = "Lista ONU no disponible"
        return out
    nombre_norm = normalizar_texto(nombre)
    individuos = lista_onu["individuos"]
    r = _verificar_contra_individuos_onu(nombre_norm, individuos)
    out["en_lista"] = r["en_lista"]
    out["similitud"] = r["similitud"]
    out["mejor_match"] = r["mejor_match"]
    out["nombres_encontrados"] = r["nombres_encontrados"]
    return out


def verificar_ofac(nombre: str, lista_ofac: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica contra lista OFAC ya descargada. Mismo formato que verificar_onu.
    """
    out = {
        "en_lista": False,
        "similitud": 0.0,
        "mejor_match": "",
        "nombres_encontrados": [],
        "error": None,
    }
    if not lista_ofac or "registros" not in lista_ofac:
        out["error"] = "Lista OFAC no disponible"
        return out
    nombre_norm = normalizar_texto(nombre)
    mejor_sim = 0.0
    for nombres_lista in lista_ofac["registros"]:
        nombre_completo = " ".join(nombres_lista) if isinstance(nombres_lista, list) else str(nombres_lista)
        sim = similitud_nombres(nombre_norm, nombre_completo)
        if sim > mejor_sim:
            mejor_sim = sim
            out["mejor_match"] = nombre_completo[:200]
        if sim >= UMBRAL_SIMILITUD:
            out["en_lista"] = True
            if nombre_completo not in out["nombres_encontrados"]:
                out["nombres_encontrados"].append(nombre_completo)
    out["similitud"] = mejor_sim
    return out


def verificar_ue(nombre: str, lista_ue: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifica contra lista UE ya descargada. Mismo formato que verificar_onu.
    """
    out = {
        "en_lista": False,
        "similitud": 0.0,
        "mejor_match": "",
        "nombres_encontrados": [],
        "error": None,
    }
    if not lista_ue or "registros" not in lista_ue:
        out["error"] = "Lista UE no disponible"
        return out
    nombre_norm = normalizar_texto(nombre)
    mejor_sim = 0.0
    for nombres_lista in lista_ue["registros"]:
        nombre_completo = " ".join(nombres_lista) if isinstance(nombres_lista, list) else str(nombres_lista)
        sim = similitud_nombres(nombre_norm, nombre_completo)
        if sim > mejor_sim:
            mejor_sim = sim
            out["mejor_match"] = nombre_completo[:200]
        if sim >= UMBRAL_SIMILITUD:
            out["en_lista"] = True
            if nombre_completo not in out["nombres_encontrados"]:
                out["nombres_encontrados"].append(nombre_completo)
    out["similitud"] = mejor_sim
    return out


# -----------------------------------------------------------------------------
# 4. Países GAFI
# -----------------------------------------------------------------------------

def verificar_pais_gafi(codigo_iso: Optional[str]) -> Dict[str, str]:
    """
    Retorna nivel de riesgo GAFI para un código ISO (ej: UY, IR, SY).
    Keys: nivel (ALTO | MEDIO | NINGUNO), codigo.
    """
    codigo = (codigo_iso or "").strip().upper()[:2]
    if not codigo:
        return {"nivel": "NINGUNO", "codigo": ""}
    if codigo in GAFI_ALTO_RIESGO:
        return {"nivel": "ALTO", "codigo": codigo}
    if codigo in GAFI_GREY_LIST:
        return {"nivel": "MEDIO", "codigo": codigo}
    return {"nivel": "NINGUNO", "codigo": codigo}
