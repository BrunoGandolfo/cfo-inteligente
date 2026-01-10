"""
API para gestión de leyes uruguayas.

Integración con CSV del Parlamento de Uruguay.
Acceso: Todos los usuarios autenticados (excepto cargar-parlamento que es solo socios).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Usuario
from app.schemas.ley import (
    LeyResponse,
    LeyDetalleResponse,
    LeyBusquedaParams,
    LeyListResponse
)
from app.services import ley_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leyes", tags=["leyes"])


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/buscar", response_model=LeyListResponse)
def buscar_leyes_por_tema(
    tema: str = Query(..., description="Tema o palabra clave para buscar"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Busca leyes por tema en título y texto completo.
    
    Solo devuelve leyes que realmente matchean el tema.
    Ordena por relevancia: primero las que tienen match en título.
    
    Ejemplo: /api/leyes/buscar?tema=despido&limit=20
    
    Acceso: Cualquier usuario autenticado.
    """
    try:
        # Construir parámetros de búsqueda
        params = LeyBusquedaParams(
            query=tema,
            limit=limit,
            offset=offset
        )
        
        # Buscar leyes
        leyes, total = ley_service.buscar_leyes(db, params)
        
        # Convertir a response
        leyes_response = [LeyResponse.model_validate(ley) for ley in leyes]
        
        return LeyListResponse(
            total=total,
            leyes=leyes_response
        )
        
    except Exception as e:
        logger.error(f"Error buscando leyes por tema '{tema}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al buscar leyes"
        )


@router.get("/", response_model=LeyListResponse)
def listar_leyes(
    query: Optional[str] = Query(None, description="Búsqueda en título y texto"),
    numero: Optional[int] = Query(None, description="Número de ley exacto"),
    anio: Optional[int] = Query(None, description="Año exacto"),
    desde_anio: Optional[int] = Query(None, description="Año desde"),
    hasta_anio: Optional[int] = Query(None, description="Año hasta"),
    solo_con_texto: bool = Query(False, description="Solo leyes con texto completo"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista leyes con filtros y paginación.
    
    Acceso: Cualquier usuario autenticado.
    """
    try:
        # Construir parámetros de búsqueda
        params = LeyBusquedaParams(
            query=query,
            numero=numero,
            anio=anio,
            desde_anio=desde_anio,
            hasta_anio=hasta_anio,
            solo_con_texto=solo_con_texto,
            limit=limit,
            offset=offset
        )
        
        # Buscar leyes
        leyes, total = ley_service.buscar_leyes(db, params)
        
        # Convertir a response
        leyes_response = [LeyResponse.model_validate(ley) for ley in leyes]
        
        return LeyListResponse(
            total=total,
            leyes=leyes_response
        )
        
    except Exception as e:
        logger.error(f"Error listando leyes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al listar leyes"
        )


@router.get("/{ley_id}", response_model=LeyResponse)
def obtener_ley(
    ley_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una ley por su ID.
    
    Acceso: Cualquier usuario autenticado.
    """
    try:
        # Validar UUID
        try:
            ley_uuid = UUID(ley_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"ID de ley inválido: {ley_id}. Formato esperado: UUID"
            )
        
        # Buscar ley
        ley = ley_service.obtener_ley_por_id(db, ley_uuid)
        
        if ley is None:
            raise HTTPException(
                status_code=404,
                detail="Ley no encontrada"
            )
        
        return LeyResponse.model_validate(ley)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ley {ley_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener ley"
        )


@router.get("/numero/{numero}", response_model=LeyDetalleResponse)
def obtener_ley_por_numero(
    numero: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una ley solo por número (sin año).
    
    Si hay varias leyes con el mismo número, devuelve la más reciente.
    Incluye texto_completo si está disponible.
    
    Ejemplo: /api/leyes/numero/19889
    
    Acceso: Cualquier usuario autenticado.
    """
    try:
        # Validar parámetros
        if numero <= 0:
            raise HTTPException(
                status_code=400,
                detail="El número de ley debe ser mayor a 0"
            )
        
        # Buscar ley
        ley = ley_service.obtener_ley_por_numero(db, numero)
        
        if ley is None:
            raise HTTPException(
                status_code=404,
                detail=f"Ley {numero} no encontrada"
            )
        
        return LeyDetalleResponse.model_validate(ley)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ley {numero}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener ley"
        )


@router.get("/numero/{numero}/anio/{anio}", response_model=LeyResponse)
def obtener_ley_por_numero_anio(
    numero: int,
    anio: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una ley por número y año.
    
    Ejemplo: /api/leyes/numero/19889/anio/2020
    
    Acceso: Cualquier usuario autenticado.
    """
    try:
        # Validar parámetros
        if numero <= 0:
            raise HTTPException(
                status_code=400,
                detail="El número de ley debe ser mayor a 0"
            )
        
        from datetime import datetime
        anio_actual = datetime.now().year
        if anio < 1935 or anio > anio_actual + 1:
            raise HTTPException(
                status_code=400,
                detail=f"El año debe estar entre 1935 y {anio_actual + 1}"
            )
        
        # Buscar ley
        ley = ley_service.obtener_ley_por_numero_anio(db, numero, anio)
        
        if ley is None:
            raise HTTPException(
                status_code=404,
                detail=f"Ley {numero}/{anio} no encontrada"
            )
        
        return LeyResponse.model_validate(ley)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ley {numero}/{anio}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno al obtener ley"
        )


@router.post("/cargar-parlamento")
def cargar_desde_parlamento(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Ejecuta carga de leyes desde CSV del Parlamento.
    
    Descarga el CSV oficial y carga/actualiza leyes en la base de datos.
    
    Acceso: SOLO socios.
    """
    # Verificar que sea socio
    if not current_user.es_socio:
        raise HTTPException(
            status_code=403,
            detail="Solo socios pueden cargar leyes desde el Parlamento"
        )
    
    try:
        logger.info(f"Iniciando carga desde Parlamento - Usuario: {current_user.email}")
        
        # Ejecutar carga
        estadisticas = ley_service.cargar_desde_csv_parlamento(db)
        
        # Construir mensaje
        mensaje = (
            f"Carga completada: {estadisticas['nuevas']} nuevas, "
            f"{estadisticas['actualizadas']} actualizadas, "
            f"{estadisticas['errores']} errores"
        )
        
        logger.info(f"Carga Parlamento completada - {mensaje}")
        
        return {
            "nuevas": estadisticas["nuevas"],
            "actualizadas": estadisticas["actualizadas"],
            "errores": estadisticas["errores"],
            "mensaje": mensaje
        }
        
    except Exception as e:
        logger.error(f"Error cargando desde Parlamento: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al cargar leyes: {str(e)}"
        )


@router.post("/{ley_id}/cargar-texto")
def cargar_texto_ley(
    ley_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Carga el texto completo de IMPO para una ley específica.
    
    Acceso: SOLO socios.
    """
    # Verificar que sea socio
    if not current_user.es_socio:
        raise HTTPException(
            status_code=403,
            detail="Solo socios pueden cargar textos de leyes"
        )
    
    try:
        # Validar UUID
        try:
            ley_uuid = UUID(ley_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"ID de ley inválido: {ley_id}. Formato esperado: UUID"
            )
        
        # Verificar que la ley existe
        ley = ley_service.obtener_ley_por_id(db, ley_uuid)
        if ley is None:
            raise HTTPException(
                status_code=404,
                detail="Ley no encontrada"
            )
        
        logger.info(f"Cargando texto de ley {ley.numero}/{ley.anio} - Usuario: {current_user.email}")
        
        # Cargar texto
        exito = ley_service.cargar_texto_ley(db, ley_uuid)
        
        if exito:
            mensaje = f"Texto cargado exitosamente para ley {ley.numero}/{ley.anio}"
            logger.info(mensaje)
            return {
                "exito": True,
                "mensaje": mensaje
            }
        else:
            mensaje = f"No se pudo cargar el texto para ley {ley.numero}/{ley.anio}"
            logger.warning(mensaje)
            return {
                "exito": False,
                "mensaje": mensaje
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cargando texto de ley {ley_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al cargar texto: {str(e)}"
        )


@router.post("/cargar-textos-lote")
def cargar_textos_lote(
    limite: int = Query(10, ge=1, le=50, description="Cantidad máxima de leyes a procesar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Carga textos completos de leyes en lote (sin texto).
    
    Útil para cargar de a poco sin saturar IMPO.
    
    Acceso: SOLO socios.
    """
    # Verificar que sea socio
    if not current_user.es_socio:
        raise HTTPException(
            status_code=403,
            detail="Solo socios pueden cargar textos de leyes"
        )
    
    try:
        logger.info(f"Iniciando carga de textos en lote (límite: {limite}) - Usuario: {current_user.email}")
        
        # Ejecutar carga en lote
        estadisticas = ley_service.cargar_textos_lote(db, limite)
        
        logger.info(
            f"Carga de textos en lote completada: "
            f"{estadisticas['exitosas']} exitosas, {estadisticas['fallidas']} fallidas"
        )
        
        return estadisticas
        
    except Exception as e:
        logger.error(f"Error cargando textos en lote: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al cargar textos: {str(e)}"
        )

