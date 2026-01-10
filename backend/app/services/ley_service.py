"""
Servicio para gestión de leyes uruguayas.

Integración con CSV del Parlamento de Uruguay.
CSV: https://parlamento.gub.uy/transparencia/datos-abiertos/leyes-promulgadas/csv
"""

import logging
import csv
import io
import requests
import json
import re
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case

from app.models.ley import Ley
from app.schemas.ley import LeyCreate, LeyBusquedaParams

logger = logging.getLogger(__name__)

# ============================================================================
# URL DEL CSV DEL PARLAMENTO
# ============================================================================

CSV_PARLAMENTO_URL = "https://parlamento.gub.uy/transparencia/datos-abiertos/leyes-promulgadas/csv"
CSV_TIMEOUT = 120  # segundos

# ============================================================================
# CONSULTAS BÁSICAS
# ============================================================================


def obtener_ley_por_id(db: Session, ley_id: UUID) -> Optional[Ley]:
    """
    Obtiene una ley por su ID.
    
    Args:
        db: Sesión de base de datos
        ley_id: UUID de la ley
        
    Returns:
        Ley si existe y no está eliminada, None en caso contrario
    """
    return db.query(Ley).filter(
        Ley.id == ley_id,
        Ley.deleted_at.is_(None)
    ).first()


def obtener_ley_por_numero_anio(db: Session, numero: int, anio: int) -> Optional[Ley]:
    """
    Busca una ley por número y año.
    
    Args:
        db: Sesión de base de datos
        numero: Número de la ley
        anio: Año de la ley
        
    Returns:
        Ley si existe y no está eliminada, None en caso contrario
    """
    return db.query(Ley).filter(
        Ley.numero == numero,
        Ley.anio == anio,
        Ley.deleted_at.is_(None)
    ).first()


def obtener_ley_por_numero(db: Session, numero: int) -> Optional[Ley]:
    """
    Busca una ley solo por número (sin año).
    
    Si hay varias leyes con el mismo número, retorna la más reciente.
    
    Args:
        db: Sesión de base de datos
        numero: Número de la ley
        
    Returns:
        Ley más reciente si existe y no está eliminada, None en caso contrario
    """
    return db.query(Ley).filter(
        Ley.numero == numero,
        Ley.deleted_at.is_(None)
    ).order_by(Ley.anio.desc(), Ley.numero.desc()).first()


# ============================================================================
# BÚSQUEDA CON FILTROS
# ============================================================================


def buscar_leyes(
    db: Session, 
    params: LeyBusquedaParams
) -> Tuple[List[Ley], int]:
    """
    Busca leyes con filtros y paginación.
    
    Args:
        db: Sesión de base de datos
        params: Parámetros de búsqueda
        
    Returns:
        Tuple (lista de leyes, total de resultados)
    """
    # Query base: excluir eliminadas
    query = db.query(Ley).filter(Ley.deleted_at.is_(None))
    
    # Filtro: búsqueda en título y texto_completo (ILIKE para case-insensitive)
    if params.query:
        # Buscar en título O texto_completo
        query = query.filter(
            or_(
                Ley.titulo.ilike(f"%{params.query}%"),
                Ley.texto_completo.ilike(f"%{params.query}%")
            )
        )
    
    # Filtro: número exacto
    if params.numero is not None:
        query = query.filter(Ley.numero == params.numero)
    
    # Filtro: año exacto
    if params.anio is not None:
        query = query.filter(Ley.anio == params.anio)
    
    # Filtro: rango de años
    if params.desde_anio is not None:
        query = query.filter(Ley.anio >= params.desde_anio)
    
    if params.hasta_anio is not None:
        query = query.filter(Ley.anio <= params.hasta_anio)
    
    # Filtro: solo con texto completo
    if params.solo_con_texto:
        query = query.filter(Ley.tiene_texto == True)
    
    # Contar total (antes de paginación)
    total = query.count()
    
    # Orden: primero las que tienen match en título, luego por año DESC, número DESC
    if params.query:
        # Ordenar por relevancia: primero las que matchean en título
        from sqlalchemy import case
        query = query.order_by(
            case(
                (Ley.titulo.ilike(f"%{params.query}%"), 0),
                else_=1
            ),
            Ley.anio.desc(),
            Ley.numero.desc()
        )
    else:
        # Orden: por año DESC, número DESC (más recientes primero)
        query = query.order_by(Ley.anio.desc(), Ley.numero.desc())
    
    # Paginación
    leyes = query.offset(params.offset).limit(params.limit).all()
    
    return leyes, total


# ============================================================================
# CREAR Y ACTUALIZAR
# ============================================================================


def crear_ley(db: Session, data: LeyCreate) -> Ley:
    """
    Crea una ley nueva o actualiza si ya existe (por número + año).
    
    Args:
        db: Sesión de base de datos
        data: Datos de la ley a crear
        
    Returns:
        Ley creada o actualizada
    """
    # Verificar si ya existe
    ley_existente = obtener_ley_por_numero_anio(db, data.numero, data.anio)
    
    if ley_existente:
        # Actualizar ley existente
        logger.info(f"Actualizando ley existente: {data.numero}/{data.anio}")
        ley_existente.titulo = data.titulo
        ley_existente.fecha_promulgacion = data.fecha_promulgacion
        ley_existente.url_parlamento = data.url_parlamento
        ley_existente.url_impo = data.url_impo
        ley_existente.leyes_referenciadas = data.leyes_referenciadas
        ley_existente.leyes_que_referencia = data.leyes_que_referencia
        # No actualizar deleted_at si estaba eliminada (restaurar)
        if ley_existente.deleted_at:
            ley_existente.deleted_at = None
        
        db.commit()
        db.refresh(ley_existente)
        return ley_existente
    
    # Crear nueva ley
    logger.info(f"Creando nueva ley: {data.numero}/{data.anio}")
    nueva_ley = Ley(
        numero=data.numero,
        anio=data.anio,
        titulo=data.titulo,
        fecha_promulgacion=data.fecha_promulgacion,
        url_parlamento=data.url_parlamento,
        url_impo=data.url_impo,
        leyes_referenciadas=data.leyes_referenciadas,
        leyes_que_referencia=data.leyes_que_referencia,
        tiene_texto=False  # Se llenará después con IMPO
    )
    
    db.add(nueva_ley)
    db.commit()
    db.refresh(nueva_ley)
    
    return nueva_ley


# ============================================================================
# CARGA DESDE CSV DEL PARLAMENTO
# ============================================================================


def _parsear_fecha(fecha_str: str) -> Optional[date]:
    """
    Parsea fecha en formato YYYY-MM-DD.
    
    Args:
        fecha_str: String con fecha
        
    Returns:
        date object o None si no se puede parsear
    """
    if not fecha_str or fecha_str.strip() == "":
        return None
    
    try:
        # Formato esperado: YYYY-MM-DD
        return datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error parseando fecha '{fecha_str}': {e}")
        return None


def _parsear_entero(valor: str, default: int = 0) -> int:
    """
    Parsea string a entero con valor por defecto.
    
    Args:
        valor: String a parsear
        default: Valor por defecto si falla
        
    Returns:
        int parseado o default
    """
    if not valor or valor.strip() == "":
        return default
    
    try:
        return int(valor.strip())
    except (ValueError, AttributeError):
        return default


def _parsear_url(url_str: str) -> Optional[str]:
    """
    Limpia y valida URL.
    
    Args:
        url_str: String con URL
        
    Returns:
        URL limpia o None si está vacía
    """
    if not url_str or url_str.strip() == "":
        return None
    
    url_limpia = url_str.strip()
    # Validar que sea una URL válida (básico)
    if url_limpia.startswith("http://") or url_limpia.startswith("https://"):
        return url_limpia
    
    return None


def cargar_desde_csv_parlamento(db: Session) -> Dict[str, int]:
    """
    Descarga y carga leyes desde el CSV del Parlamento.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Dict con estadísticas:
        {
            "nuevas": int,
            "actualizadas": int,
            "errores": int
        }
    """
    logger.info(f"Descargando CSV del Parlamento: {CSV_PARLAMENTO_URL}")
    
    estadisticas = {
        "nuevas": 0,
        "actualizadas": 0,
        "errores": 0
    }
    
    try:
        # Descargar CSV
        response = requests.get(CSV_PARLAMENTO_URL, timeout=CSV_TIMEOUT)
        response.raise_for_status()
        
        # Decodificar contenido (asumiendo UTF-8)
        contenido = response.content.decode('utf-8')
        logger.info(f"CSV descargado: {len(contenido)} caracteres")
        
        # Parsear CSV
        reader = csv.DictReader(io.StringIO(contenido))
        
        # Verificar que tenga las columnas esperadas
        columnas_esperadas = [
            "Fecha", "Numero_de_Ley", "Texto_Original", "Texto_Actualizado",
            "Titulo", "Asunto", "Leyes_Referenciadas", "Leyes_que_referencia"
        ]
        
        columnas_csv = reader.fieldnames
        if not columnas_csv:
            logger.error("CSV vacío o sin columnas")
            estadisticas["errores"] = 1
            return estadisticas
        
        # Verificar columnas críticas
        if "Numero_de_Ley" not in columnas_csv or "Titulo" not in columnas_csv:
            logger.error(f"CSV no tiene columnas esperadas. Columnas encontradas: {columnas_csv}")
            estadisticas["errores"] = 1
            return estadisticas
        
        # Procesar cada fila
        for fila_num, fila in enumerate(reader, start=2):  # start=2 porque la fila 1 es header
            try:
                # Extraer y validar número de ley
                numero_str = fila.get("Numero_de_Ley", "").strip()
                if not numero_str:
                    logger.warning(f"Fila {fila_num}: Numero_de_Ley vacío, saltando")
                    estadisticas["errores"] += 1
                    continue
                
                numero = _parsear_entero(numero_str)
                if numero <= 0:
                    logger.warning(f"Fila {fila_num}: Numero_de_Ley inválido ({numero_str}), saltando")
                    estadisticas["errores"] += 1
                    continue
                
                # Extraer fecha y año
                fecha_str = fila.get("Fecha", "").strip()
                fecha_promulgacion = _parsear_fecha(fecha_str)
                
                # Si no hay fecha, intentar extraer año del número o usar año actual
                if fecha_promulgacion:
                    anio = fecha_promulgacion.year
                else:
                    # Intentar inferir año (puede estar en otro campo o usar año actual)
                    logger.warning(f"Fila {fila_num}: Sin fecha, usando año actual")
                    anio = datetime.now().year
                
                # Validar año
                anio_actual = datetime.now().year
                if anio < 1935 or anio > anio_actual + 1:
                    logger.warning(f"Fila {fila_num}: Año inválido ({anio}), saltando")
                    estadisticas["errores"] += 1
                    continue
                
                # Extraer título (obligatorio)
                titulo = fila.get("Titulo", "").strip()
                if not titulo:
                    logger.warning(f"Fila {fila_num}: Titulo vacío, saltando")
                    estadisticas["errores"] += 1
                    continue
                
                # Extraer URLs
                url_parlamento = _parsear_url(fila.get("Texto_Original", ""))
                url_impo = _parsear_url(fila.get("Texto_Actualizado", ""))
                
                # Extraer contadores de referencias
                leyes_referenciadas = _parsear_entero(fila.get("Leyes_Referenciadas", "0"))
                leyes_que_referencia = _parsear_entero(fila.get("Leyes_que_referencia", "0"))
                
                # Crear schema y guardar
                ley_data = LeyCreate(
                    numero=numero,
                    anio=anio,
                    titulo=titulo,
                    fecha_promulgacion=fecha_promulgacion,
                    url_parlamento=url_parlamento,
                    url_impo=url_impo,
                    leyes_referenciadas=leyes_referenciadas,
                    leyes_que_referencia=leyes_que_referencia
                )
                
                # Verificar si es nueva o actualización
                ley_existente = obtener_ley_por_numero_anio(db, numero, anio)
                es_nueva = ley_existente is None
                
                # Crear o actualizar
                ley = crear_ley(db, ley_data)
                
                if es_nueva:
                    estadisticas["nuevas"] += 1
                else:
                    estadisticas["actualizadas"] += 1
                
                # Log cada 100 leyes procesadas
                if (estadisticas["nuevas"] + estadisticas["actualizadas"]) % 100 == 0:
                    logger.info(f"Procesadas {estadisticas['nuevas'] + estadisticas['actualizadas']} leyes...")
                
            except Exception as e:
                logger.error(f"Error procesando fila {fila_num}: {e}", exc_info=True)
                estadisticas["errores"] += 1
                continue
        
        logger.info(
            f"Carga CSV completada: {estadisticas['nuevas']} nuevas, "
            f"{estadisticas['actualizadas']} actualizadas, {estadisticas['errores']} errores"
        )
        
    except requests.RequestException as e:
        logger.error(f"Error descargando CSV del Parlamento: {e}")
        estadisticas["errores"] = 1
    except Exception as e:
        logger.error(f"Error inesperado cargando CSV: {e}", exc_info=True)
        estadisticas["errores"] = 1
    
    return estadisticas


# ============================================================================
# CARGA DE TEXTO COMPLETO DESDE IMPO
# ============================================================================


def sanitizar_json(texto: str) -> str:
    """
    Elimina TODOS los caracteres de control inválidos del JSON.
    
    Elimina caracteres de control ASCII (0x00-0x1F) excepto newlines.
    Reemplaza \r y \t por espacio.
    
    Args:
        texto: Texto JSON crudo
        
    Returns:
        Texto JSON sanitizado
    """
    # Elimina caracteres de control ASCII (0x00-0x1F) excepto newlines
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', texto)
    # Reemplaza \r y \t por espacio
    texto = texto.replace('\r', ' ').replace('\t', ' ')
    return texto


def obtener_texto_impo(url_impo: str) -> Optional[str]:
    """
    Descarga el texto completo de una ley desde IMPO.
    
    Args:
        url_impo: URL de la ley en IMPO (ej: https://www.impo.com.uy/bases/leyes/19889-2020)
        
    Returns:
        Texto completo concatenado de todos los artículos, o None si falla
    """
    if not url_impo:
        logger.warning("URL de IMPO vacía")
        return None
    
    try:
        # Agregar ?json=true a la URL
        url_json = f"{url_impo}?json=true" if "?" not in url_impo else f"{url_impo}&json=true"
        
        logger.info(f"Descargando texto de IMPO: {url_json}")
        
        # Descargar JSON con timeout
        response = requests.get(url_json, timeout=30)
        response.raise_for_status()
        
        texto_raw = response.text.strip()
        
        # Detectar si IMPO devuelve HTML en lugar de JSON
        if texto_raw.startswith('<') or texto_raw.startswith('<!'):
            logger.warning(f"IMPO devuelve HTML en lugar de JSON para {url_impo}")
            return None
        
        # Solo continuar si parece JSON
        if not texto_raw.startswith('{'):
            logger.warning(f"Respuesta inesperada de IMPO (no es JSON): {url_impo}")
            return None
        
        # FIX: Sanitizar JSON antes de parsear (elimina caracteres de control inválidos)
        texto_limpio = sanitizar_json(texto_raw)
        
        # Parsear JSON sanitizado
        data = json.loads(texto_limpio)
        
        # Extraer artículos
        articulos = data.get("articulos", [])
        
        if not articulos:
            logger.warning(f"No se encontraron artículos en la respuesta de IMPO: {url_impo}")
            return None
        
        # Concatenar texto de todos los artículos
        textos = []
        for articulo in articulos:
            nro_articulo = articulo.get("nroArticulo", "")
            texto_articulo = articulo.get("textoArticulo", "")
            
            if texto_articulo:
                # Agregar número de artículo si existe
                if nro_articulo:
                    textos.append(f"Artículo {nro_articulo}\n{texto_articulo}")
                else:
                    textos.append(texto_articulo)
        
        texto_completo = "\n\n".join(textos)
        
        logger.info(f"Texto descargado exitosamente: {len(texto_completo)} caracteres")
        return texto_completo
        
    except requests.RequestException as e:
        logger.error(f"Error descargando texto de IMPO ({url_impo}): {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON de IMPO ({url_impo}): {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado obteniendo texto de IMPO ({url_impo}): {e}", exc_info=True)
        return None


def cargar_texto_ley(db: Session, ley_id: UUID) -> bool:
    """
    Carga el texto completo de una ley desde IMPO.
    
    Args:
        db: Sesión de base de datos
        ley_id: UUID de la ley
        
    Returns:
        True si se cargó exitosamente, False si falló
    """
    try:
        # Buscar ley
        ley = obtener_ley_por_id(db, ley_id)
        
        if ley is None:
            logger.error(f"Ley no encontrada: {ley_id}")
            return False
        
        # Si ya tiene texto, no recargar
        if ley.tiene_texto:
            logger.info(f"Ley {ley.numero}/{ley.anio} ya tiene texto, omitiendo")
            return True
        
        # Verificar que tenga URL de IMPO
        if not ley.url_impo:
            logger.warning(f"Ley {ley.numero}/{ley.anio} no tiene URL de IMPO")
            return False
        
        # Obtener texto de IMPO
        texto_completo = obtener_texto_impo(ley.url_impo)
        
        if texto_completo is None:
            logger.warning(f"No se pudo obtener texto de IMPO para ley {ley.numero}/{ley.anio}")
            return False
        
        # Actualizar ley
        ley.texto_completo = texto_completo
        ley.tiene_texto = True
        
        db.commit()
        db.refresh(ley)
        
        logger.info(f"Texto cargado exitosamente para ley {ley.numero}/{ley.anio}")
        return True
        
    except Exception as e:
        logger.error(f"Error cargando texto de ley {ley_id}: {e}", exc_info=True)
        db.rollback()
        return False


def cargar_textos_lote(db: Session, limite: int = 10) -> Dict[str, int]:
    """
    Carga textos completos de leyes en lote (sin texto).
    
    Útil para cargar de a poco sin saturar IMPO.
    
    Args:
        db: Sesión de base de datos
        limite: Cantidad máxima de leyes a procesar
        
    Returns:
        Dict con estadísticas: {"exitosas": N, "fallidas": M}
    """
    logger.info(f"Iniciando carga de textos en lote (límite: {limite})")
    
    estadisticas = {
        "exitosas": 0,
        "fallidas": 0
    }
    
    try:
        # Buscar leyes sin texto
        leyes_sin_texto = db.query(Ley).filter(
            Ley.tiene_texto == False,
            Ley.deleted_at.is_(None),
            Ley.url_impo.isnot(None)  # Solo las que tienen URL de IMPO
        ).limit(limite).all()
        
        if not leyes_sin_texto:
            logger.info("No hay leyes pendientes de cargar texto")
            return estadisticas
        
        logger.info(f"Procesando {len(leyes_sin_texto)} leyes sin texto")
        
        # Procesar cada ley
        for ley in leyes_sin_texto:
            try:
                exito = cargar_texto_ley(db, ley.id)
                
                if exito:
                    estadisticas["exitosas"] += 1
                else:
                    estadisticas["fallidas"] += 1
                    
            except Exception as e:
                logger.error(f"Error procesando ley {ley.id}: {e}", exc_info=True)
                estadisticas["fallidas"] += 1
                continue
        
        logger.info(
            f"Carga de textos en lote completada: "
            f"{estadisticas['exitosas']} exitosas, {estadisticas['fallidas']} fallidas"
        )
        
    except Exception as e:
        logger.error(f"Error inesperado en carga de textos en lote: {e}", exc_info=True)
    
    return estadisticas

