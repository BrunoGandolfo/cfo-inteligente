"""
Router de Indicadores Económicos de Uruguay.

Expone endpoints para obtener:
- UI (Unidad Indexada)
- UR (Unidad Reajustable)
- IPC (Índice de Precios al Consumo)
- BPC (Base de Prestaciones y Contribuciones)
- Cotizaciones de monedas (USD, EUR, BRL)

Todos los endpoints requieren autenticación JWT.
"""

from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services import indicadores_service
from app.schemas.indicadores import (
    IndicadorResponse,
    CotizacionesResponse,
    IndicadoresTodosResponse,
)

router = APIRouter(prefix="/api/indicadores", tags=["Indicadores Económicos"])


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS INDIVIDUALES
# ═══════════════════════════════════════════════════════════════

@router.get("/ui", response_model=IndicadorResponse)
def obtener_ui(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene el valor de la Unidad Indexada (UI).
    
    La UI es un índice de ajuste diario basado en la inflación.
    Fuente: BCU / INE
    """
    return indicadores_service.obtener_ui()


@router.get("/ur", response_model=IndicadorResponse)
def obtener_ur(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene el valor de la Unidad Reajustable (UR).
    
    La UR se ajusta mensualmente según el Índice Medio de Salarios.
    Fuente: BCU
    """
    return indicadores_service.obtener_ur()


@router.get("/bpc", response_model=IndicadorResponse)
def obtener_bpc(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene la Base de Prestaciones y Contribuciones (BPC).
    
    La BPC es la unidad de medida para prestaciones sociales.
    Fuente: BPS
    """
    return indicadores_service.obtener_bpc()


@router.get("/inflacion", response_model=IndicadorResponse)
def obtener_inflacion(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene la inflación anual acumulada (últimos 12 meses).
    
    Fuente: INE
    """
    return indicadores_service.obtener_inflacion()


@router.get("/cotizaciones", response_model=CotizacionesResponse)
def obtener_cotizaciones(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene las cotizaciones de monedas (USD, EUR, BRL).
    
    Retorna valores de compra y venta para cada moneda.
    Fuente: DolarApi
    """
    return indicadores_service.obtener_cotizaciones()


# ═══════════════════════════════════════════════════════════════
# ENDPOINT AGREGADO
# ═══════════════════════════════════════════════════════════════

@router.get("/todos", response_model=IndicadoresTodosResponse)
def obtener_todos(current_user: Usuario = Depends(get_current_user)):
    """
    Obtiene todos los indicadores económicos en una sola llamada.
    
    Incluye: UI, UR, IPC, BPC, inflación y cotizaciones de monedas.
    Útil para cargar el dashboard de indicadores.
    """
    return indicadores_service.obtener_todos_indicadores()
