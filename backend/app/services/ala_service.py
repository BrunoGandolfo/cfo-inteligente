"""
Servicio orquestador ALA (Anti-Lavado de Activos).

Coordina verificaciones de debida diligencia contra listas:
PEP (Uruguay), ONU, OFAC (EE.UU.), UE, GAFI.

Decreto 379/018, Arts. 17-18, 44.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.verificacion_ala import ListaALAMetadata, VerificacionALA
from app.schemas.verificacion_ala import VerificacionALACreate
from app.services.ala_list_parser import (
    descargar_lista_ofac,
    descargar_lista_onu,
    descargar_lista_pep,
    descargar_lista_ue,
    normalizar_texto,
    verificar_ofac,
    verificar_onu,
    verificar_pais_gafi,
    verificar_pep,
    verificar_ue,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constantes
# =============================================================================

LISTAS = ["PEP", "ONU", "OFAC", "UE"]

URL_FUENTES = {
    "PEP": "https://catalogodatos.gub.uy/dataset/pep",
    "ONU": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
    "OFAC": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML",
    "UE": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content",
}


# =============================================================================
# Funciones privadas
# =============================================================================

def _clasificar_riesgo(
    resultado_pep: Dict[str, Any],
    resultado_onu: Dict[str, Any],
    resultado_ofac: Dict[str, Any],
    resultado_ue: Dict[str, Any],
    resultado_gafi: Dict[str, Any],
    listas_fallidas: List[str],
) -> Dict[str, Any]:
    """
    Clasifica nivel de riesgo, diligencia y capacidad de operar.

    Reglas Decreto 379/018, Arts. 17-18, 44:

    NIVEL DE RIESGO:
    - CRITICO: match en lista ONU, OFAC o UE (sanciones internacionales)
    - ALTO: es PEP, o país GAFI alto riesgo
    - MEDIO: país GAFI grey list
    - BAJO: ninguno de los anteriores

    PUEDE OPERAR:
    - False SOLO si match en lista de sanciones (ONU, OFAC, UE)
    - True en todos los demás casos (incluyendo PEP — Art. 44 diligencia intensificada)

    NIVEL DE DILIGENCIA:
    - Si riesgo CRITICO: "INTENSIFICADA" (pero no puede operar)
    - Si riesgo ALTO: "INTENSIFICADA"
    - Si riesgo MEDIO: "NORMAL"
    - Si riesgo BAJO y NINGUNA lista falló: "SIMPLIFICADA"
    - Si riesgo BAJO pero ALGUNA lista falló en descarga: "NORMAL"

    Args:
        resultado_pep: Dict con 'es_pep': bool
        resultado_onu: Dict con 'en_lista': bool
        resultado_ofac: Dict con 'en_lista': bool
        resultado_ue: Dict con 'en_lista': bool
        resultado_gafi: Dict con 'nivel': str ('ALTO', 'MEDIO', 'NINGUNO')
        listas_fallidas: Lista de nombres de listas que fallaron en descarga

    Returns:
        Dict con:
        - nivel_riesgo: str
        - nivel_diligencia: str
        - puede_operar: bool
        - factores: List[str] (razones que contribuyeron al nivel)
    """
    factores: List[str] = []

    # Extraer valores con defaults seguros
    en_onu = resultado_onu.get("en_lista", False) if resultado_onu else False
    en_ofac = resultado_ofac.get("en_lista", False) if resultado_ofac else False
    en_ue = resultado_ue.get("en_lista", False) if resultado_ue else False
    es_pep = resultado_pep.get("es_pep", False) if resultado_pep else False
    nivel_gafi = resultado_gafi.get("nivel", "NINGUNO") if resultado_gafi else "NINGUNO"

    # Determinar nivel de riesgo
    nivel_riesgo = "BAJO"
    puede_operar = True

    # CRITICO: match en lista de sanciones
    if en_onu or en_ofac or en_ue:
        nivel_riesgo = "CRITICO"
        puede_operar = False
        if en_onu:
            factores.append("Match en lista ONU")
        if en_ofac:
            factores.append("Match en lista OFAC")
        if en_ue:
            factores.append("Match en lista UE")

    # ALTO: PEP o GAFI alto (si no es CRITICO)
    elif es_pep or nivel_gafi == "ALTO":
        nivel_riesgo = "ALTO"
        if es_pep:
            factores.append("Es Persona Políticamente Expuesta (PEP)")
        if nivel_gafi == "ALTO":
            factores.append("País de alto riesgo GAFI")

    # MEDIO: GAFI grey list
    elif nivel_gafi == "MEDIO":
        nivel_riesgo = "MEDIO"
        factores.append("País en lista gris GAFI")

    # BAJO: ninguno de los anteriores
    else:
        nivel_riesgo = "BAJO"
        if not factores:
            factores.append("Sin factores de riesgo identificados")

    # Determinar nivel de diligencia
    if nivel_riesgo in ("CRITICO", "ALTO"):
        nivel_diligencia = "INTENSIFICADA"
    elif nivel_riesgo == "MEDIO":
        nivel_diligencia = "NORMAL"
    elif nivel_riesgo == "BAJO":
        if listas_fallidas:
            nivel_diligencia = "NORMAL"
            factores.append(f"Verificación incompleta: listas no disponibles ({', '.join(listas_fallidas)})")
        else:
            nivel_diligencia = "SIMPLIFICADA"

    return {
        "nivel_riesgo": nivel_riesgo,
        "nivel_diligencia": nivel_diligencia,
        "puede_operar": puede_operar,
        "factores": factores,
    }


def _generar_hash_verificacion(
    nombre: str,
    documento: Optional[str],
    fecha_hora: datetime,
    resultados: Dict[str, Any],
) -> str:
    """Genera SHA256 de: nombre + documento + fecha_hora + resultados serializados."""
    data = f"{nombre}|{documento or ''}|{fecha_hora.isoformat()}|{json.dumps(resultados, sort_keys=True, default=str)}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _upsert_lista_metadata(
    db: Session,
    nombre_lista: str,
    resultado: Optional[Dict[str, Any]],
    error: Optional[str] = None,
) -> None:
    """
    Upsert de metadata de lista ALA.

    Si existe registro para nombre_lista, actualiza.
    Si no existe, crea nuevo registro.
    """
    ahora = datetime.now(timezone.utc)

    # Buscar existente
    metadata = db.query(ListaALAMetadata).filter(
        ListaALAMetadata.nombre_lista == nombre_lista
    ).first()

    if metadata is None:
        metadata = ListaALAMetadata(nombre_lista=nombre_lista)
        db.add(metadata)

    metadata.url_fuente = URL_FUENTES.get(nombre_lista)

    if resultado is not None:
        metadata.estado = "ACTUALIZADA"
        metadata.hash_contenido = resultado.get("hash")
        metadata.cantidad_registros = resultado.get("total")
        metadata.ultima_descarga = ahora
        metadata.error_detalle = None
    else:
        metadata.estado = "ERROR"
        metadata.error_detalle = error or "Error desconocido"


def _formatear_resultado_lista(
    nombre_lista: str,
    resultado_verificacion: Optional[Dict[str, Any]],
    hash_lista: Optional[str],
    checked: bool,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Formatea resultado de verificación para guardar en JSONB.

    Compatible con ResultadoListaSchema.
    """
    ahora = datetime.now(timezone.utc).isoformat()

    if not checked or resultado_verificacion is None:
        return {
            "checked": False,
            "hits": 0,
            "mejor_match": None,
            "similitud": None,
            "timestamp": ahora,
            "hash_lista": None,
            "error": error or "Lista no disponible",
        }

    # Contar hits
    hits = 0
    if nombre_lista == "PEP":
        hits = 1 if resultado_verificacion.get("es_pep") else 0
    elif nombre_lista == "GAFI":
        hits = 1 if resultado_verificacion.get("nivel") in ("ALTO", "MEDIO") else 0
    else:
        # ONU, OFAC, UE
        hits = 1 if resultado_verificacion.get("en_lista") else 0
        nombres_encontrados = resultado_verificacion.get("nombres_encontrados", [])
        if nombres_encontrados:
            hits = len(nombres_encontrados)

    return {
        "checked": True,
        "hits": hits,
        "mejor_match": resultado_verificacion.get("mejor_match"),
        "similitud": resultado_verificacion.get("similitud"),
        "timestamp": ahora,
        "hash_lista": hash_lista,
        "error": resultado_verificacion.get("error"),
    }


# =============================================================================
# Funciones públicas
# =============================================================================

def ejecutar_verificacion_completa(
    db: Session,
    datos: VerificacionALACreate,
    usuario_id: UUID,
) -> VerificacionALA:
    """
    Ejecuta verificación completa ALA contra todas las listas.

    Flujo:
    1. Descarga las 4 listas (PEP, ONU, OFAC, UE)
    2. Actualiza metadata de cada lista en BD
    3. Ejecuta verificaciones con las listas disponibles
    4. Clasifica nivel de riesgo y diligencia
    5. Genera hash de verificación
    6. Crea registro en BD

    Args:
        db: Sesión de SQLAlchemy
        datos: VerificacionALACreate con datos de persona
        usuario_id: UUID del usuario que ejecuta

    Returns:
        VerificacionALA creada en BD
    """
    logger.info(f"Iniciando verificación ALA para: {datos.nombre_completo[:50]}...")

    ahora = datetime.now(timezone.utc)
    nombre_normalizado = normalizar_texto(datos.nombre_completo)
    listas_fallidas: List[str] = []

    # -------------------------------------------------------------------------
    # 1. Descargar listas
    # -------------------------------------------------------------------------
    logger.info("Descargando listas ALA...")

    # PEP
    lista_pep = None
    try:
        lista_pep = descargar_lista_pep()
        if lista_pep:
            _upsert_lista_metadata(db, "PEP", lista_pep)
            logger.info(f"PEP: {lista_pep['total']} registros")
        else:
            _upsert_lista_metadata(db, "PEP", None, "Descarga retornó None")
            listas_fallidas.append("PEP")
    except Exception as e:
        logger.warning(f"Error descargando PEP: {e}")
        _upsert_lista_metadata(db, "PEP", None, str(e))
        listas_fallidas.append("PEP")

    # ONU
    lista_onu = None
    try:
        lista_onu = descargar_lista_onu()
        if lista_onu:
            _upsert_lista_metadata(db, "ONU", lista_onu)
            logger.info(f"ONU: {lista_onu['total']} individuos")
        else:
            _upsert_lista_metadata(db, "ONU", None, "Descarga retornó None")
            listas_fallidas.append("ONU")
    except Exception as e:
        logger.warning(f"Error descargando ONU: {e}")
        _upsert_lista_metadata(db, "ONU", None, str(e))
        listas_fallidas.append("ONU")

    # OFAC
    lista_ofac = None
    try:
        lista_ofac = descargar_lista_ofac()
        if lista_ofac:
            _upsert_lista_metadata(db, "OFAC", lista_ofac)
            logger.info(f"OFAC: {lista_ofac['total']} registros")
        else:
            _upsert_lista_metadata(db, "OFAC", None, "Descarga retornó None")
            listas_fallidas.append("OFAC")
    except Exception as e:
        logger.warning(f"Error descargando OFAC: {e}")
        _upsert_lista_metadata(db, "OFAC", None, str(e))
        listas_fallidas.append("OFAC")

    # UE
    lista_ue = None
    try:
        lista_ue = descargar_lista_ue()
        if lista_ue:
            _upsert_lista_metadata(db, "UE", lista_ue)
            logger.info(f"UE: {lista_ue['total']} registros")
        else:
            _upsert_lista_metadata(db, "UE", None, "Descarga retornó None")
            listas_fallidas.append("UE")
    except Exception as e:
        logger.warning(f"Error descargando UE: {e}")
        _upsert_lista_metadata(db, "UE", None, str(e))
        listas_fallidas.append("UE")

    # -------------------------------------------------------------------------
    # 2. Ejecutar verificaciones
    # -------------------------------------------------------------------------
    logger.info("Ejecutando verificaciones contra listas...")

    # PEP
    resultado_pep_raw = None
    if lista_pep:
        resultado_pep_raw = verificar_pep(
            ci=datos.numero_documento,
            nombre=nombre_normalizado,
            lista_pep=lista_pep,
        )
        logger.info(f"PEP: es_pep={resultado_pep_raw.get('es_pep')}")

    # ONU
    resultado_onu_raw = None
    if lista_onu:
        resultado_onu_raw = verificar_onu(nombre_normalizado, lista_onu)
        logger.info(f"ONU: en_lista={resultado_onu_raw.get('en_lista')}")

    # OFAC
    resultado_ofac_raw = None
    if lista_ofac:
        resultado_ofac_raw = verificar_ofac(nombre_normalizado, lista_ofac)
        logger.info(f"OFAC: en_lista={resultado_ofac_raw.get('en_lista')}")

    # UE
    resultado_ue_raw = None
    if lista_ue:
        resultado_ue_raw = verificar_ue(nombre_normalizado, lista_ue)
        logger.info(f"UE: en_lista={resultado_ue_raw.get('en_lista')}")

    # GAFI (no requiere descarga)
    resultado_gafi_raw = verificar_pais_gafi(datos.nacionalidad)
    logger.info(f"GAFI: nivel={resultado_gafi_raw.get('nivel')}")

    # -------------------------------------------------------------------------
    # 3. Clasificar riesgo
    # -------------------------------------------------------------------------
    clasificacion = _clasificar_riesgo(
        resultado_pep=resultado_pep_raw or {},
        resultado_onu=resultado_onu_raw or {},
        resultado_ofac=resultado_ofac_raw or {},
        resultado_ue=resultado_ue_raw or {},
        resultado_gafi=resultado_gafi_raw,
        listas_fallidas=listas_fallidas,
    )

    logger.info(
        f"Clasificación: riesgo={clasificacion['nivel_riesgo']}, "
        f"diligencia={clasificacion['nivel_diligencia']}, "
        f"puede_operar={clasificacion['puede_operar']}"
    )

    # -------------------------------------------------------------------------
    # 4. Formatear resultados para JSONB
    # -------------------------------------------------------------------------
    resultado_pep = _formatear_resultado_lista(
        "PEP",
        resultado_pep_raw,
        lista_pep.get("hash") if lista_pep else None,
        checked=lista_pep is not None,
    )
    resultado_onu = _formatear_resultado_lista(
        "ONU",
        resultado_onu_raw,
        lista_onu.get("hash") if lista_onu else None,
        checked=lista_onu is not None,
    )
    resultado_ofac = _formatear_resultado_lista(
        "OFAC",
        resultado_ofac_raw,
        lista_ofac.get("hash") if lista_ofac else None,
        checked=lista_ofac is not None,
    )
    resultado_ue = _formatear_resultado_lista(
        "UE",
        resultado_ue_raw,
        lista_ue.get("hash") if lista_ue else None,
        checked=lista_ue is not None,
    )
    resultado_gafi = _formatear_resultado_lista(
        "GAFI",
        resultado_gafi_raw,
        None,  # GAFI no tiene hash
        checked=True,  # GAFI siempre está disponible (lista local)
    )

    # -------------------------------------------------------------------------
    # 5. Generar hash de verificación
    # -------------------------------------------------------------------------
    resultados_para_hash = {
        "pep": resultado_pep,
        "onu": resultado_onu,
        "ofac": resultado_ofac,
        "ue": resultado_ue,
        "gafi": resultado_gafi,
        "clasificacion": clasificacion,
    }
    hash_verificacion = _generar_hash_verificacion(
        datos.nombre_completo,
        datos.numero_documento,
        ahora,
        resultados_para_hash,
    )

    # -------------------------------------------------------------------------
    # 6. Crear registro en BD
    # -------------------------------------------------------------------------
    es_pep = resultado_pep_raw.get("es_pep", False) if resultado_pep_raw else False

    verificacion = VerificacionALA(
        nombre_completo=datos.nombre_completo,
        tipo_documento=datos.tipo_documento,
        numero_documento=datos.numero_documento,
        nacionalidad=datos.nacionalidad,
        fecha_nacimiento=datos.fecha_nacimiento,
        es_persona_juridica=datos.es_persona_juridica,
        razon_social=datos.razon_social,
        nivel_diligencia=clasificacion["nivel_diligencia"],
        nivel_riesgo=clasificacion["nivel_riesgo"],
        es_pep=es_pep,
        resultado_onu=resultado_onu,
        resultado_pep=resultado_pep,
        resultado_ofac=resultado_ofac,
        resultado_ue=resultado_ue,
        resultado_gafi=resultado_gafi,
        hash_verificacion=hash_verificacion,
        expediente_id=datos.expediente_id,
        contrato_id=datos.contrato_id,
        usuario_id=usuario_id,
    )

    db.add(verificacion)
    db.commit()
    db.refresh(verificacion)

    logger.info(f"Verificación ALA creada: id={verificacion.id}, riesgo={verificacion.nivel_riesgo}")

    return verificacion


def obtener_verificacion(
    db: Session,
    verificacion_id: UUID,
) -> Optional[VerificacionALA]:
    """
    Obtiene una verificación ALA por ID.

    Args:
        db: Sesión de SQLAlchemy
        verificacion_id: UUID de la verificación

    Returns:
        VerificacionALA o None si no existe o está eliminada
    """
    return db.query(VerificacionALA).filter(
        VerificacionALA.id == verificacion_id,
        VerificacionALA.deleted_at.is_(None),
    ).first()


def listar_verificaciones(
    db: Session,
    usuario_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Lista verificaciones ALA con paginación.

    Args:
        db: Sesión de SQLAlchemy
        usuario_id: Filtrar por usuario (opcional)
        limit: Máximo de resultados (default 50)
        offset: Desplazamiento para paginación

    Returns:
        Dict con:
        - total: int (total sin paginación)
        - verificaciones: List[VerificacionALA]
        - limit: int
        - offset: int
    """
    query = db.query(VerificacionALA).filter(
        VerificacionALA.deleted_at.is_(None)
    )

    if usuario_id is not None:
        query = query.filter(VerificacionALA.usuario_id == usuario_id)

    total = query.count()

    verificaciones = query.order_by(
        VerificacionALA.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "verificaciones": verificaciones,
        "limit": limit,
        "offset": offset,
    }


def obtener_metadata_listas(db: Session) -> List[ListaALAMetadata]:
    """
    Obtiene metadata de todas las listas ALA.

    Args:
        db: Sesión de SQLAlchemy

    Returns:
        Lista de ListaALAMetadata ordenada por nombre_lista
    """
    return db.query(ListaALAMetadata).order_by(
        ListaALAMetadata.nombre_lista
    ).all()
