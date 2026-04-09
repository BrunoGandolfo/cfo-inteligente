"""
Servicio de Indicadores Económicos de Uruguay.

Indicadores con valores actualizables manualmente:
- UI (Unidad Indexada): actualización diaria
- UR (Unidad Reajustable): actualización mensual
- IPC (Índice de Precios): actualización mensual
- BPC (Base Prestaciones): actualización anual

Cotizaciones con API en tiempo real:
- USD: DolarApi

TODO: Integrar con API del INE cuando esté disponible.
"""

from datetime import datetime
from typing import Dict, Any

from app.core.logger import get_logger
from app.services.tipo_cambio_service import obtener_tipo_cambio_actual

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════
# VALORES ACTUALES (actualizar manualmente)
# ═══════════════════════════════════════════════════════════════

# Última actualización: 2026-01-04
VALORES_ACTUALES = {
    "ui": {
        "valor": 6.4243,
        "fecha": "2026-01-04",
        "frecuencia": "diaria",
    },
    "ur": {
        "valor": 1841.56,
        "fecha": "2026-01-01",
        "frecuencia": "mensual",
    },
    "bpc": {
        "valor": 6576.0,
        "fecha": "2026-01-01",
        "frecuencia": "anual",
    },
    "inflacion": {
        "valor": 5.5,
        "fecha": "2025-12-01",
        "frecuencia": "mensual",
        "nota": "Inflación anual acumulada (últimos 12 meses)",
    },
}

# ═══════════════════════════════════════════════════════════════
# INDICADORES FIJOS (UI, UR, IPC, BPC)
# ═══════════════════════════════════════════════════════════════

def obtener_ui() -> Dict[str, Any]:
    """
    Obtiene el valor de la Unidad Indexada (UI).
    
    Valor fijo actualizable manualmente.
    Fuente: INE (https://www.ine.gub.uy)
    Frecuencia: Diaria
    """
    return {
        "valor": VALORES_ACTUALES["ui"]["valor"],
        "fecha": VALORES_ACTUALES["ui"]["fecha"],
        "fuente": "INE (manual)",
    }


def obtener_ur() -> Dict[str, Any]:
    """
    Obtiene el valor de la Unidad Reajustable (UR).
    
    Valor fijo actualizable manualmente.
    Fuente: INE (https://www.ine.gub.uy)
    Frecuencia: Mensual
    """
    return {
        "valor": VALORES_ACTUALES["ur"]["valor"],
        "fecha": VALORES_ACTUALES["ur"]["fecha"],
        "fuente": "INE (manual)",
    }


def obtener_bpc() -> Dict[str, Any]:
    """
    Obtiene la Base de Prestaciones y Contribuciones (BPC).
    
    Valor fijo actualizable manualmente.
    Fuente: BPS (https://www.bps.gub.uy)
    Frecuencia: Anual (se actualiza en enero)
    """
    return {
        "valor": VALORES_ACTUALES["bpc"]["valor"],
        "fecha": VALORES_ACTUALES["bpc"]["fecha"],
        "fuente": "BPS (manual)",
    }


def obtener_inflacion() -> Dict[str, Any]:
    """
    Obtiene la inflación anual acumulada (últimos 12 meses).
    
    Valor fijo actualizable manualmente.
    Fuente: INE (https://www.ine.gub.uy)
    Frecuencia: Mensual
    """
    return {
        "valor": VALORES_ACTUALES["inflacion"]["valor"],
        "fecha": VALORES_ACTUALES["inflacion"]["fecha"],
        "fuente": "INE (manual)",
    }


# ═══════════════════════════════════════════════════════════════
# COTIZACIONES DE MONEDAS
# ═══════════════════════════════════════════════════════════════


def obtener_cotizaciones() -> Dict[str, Any]:
    """
    Obtiene la cotización de USD.
    
    Fuente: tipo_cambio_service -> DolarApi/fallback
    Cache: delegada a tipo_cambio_service
    """
    datos_usd = obtener_tipo_cambio_actual()
    logger.info("Cotizaciones obtenidas desde tipo_cambio_service")
    return {
        "usd": {
            "compra": datos_usd["compra"],
            "venta": datos_usd["venta"],
        },
        "timestamp": datos_usd["actualizado"],
    }


# ═══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: TODOS LOS INDICADORES
# ═══════════════════════════════════════════════════════════════

def obtener_todos_indicadores() -> Dict[str, Any]:
    """
    Obtiene todos los indicadores económicos en una sola llamada.
    
    Returns:
        Dict con ui, ur, ipc, bpc, inflacion, cotizaciones y timestamp
    """
    return {
        "ui": obtener_ui(),
        "ur": obtener_ur(),
        "bpc": obtener_bpc(),
        "inflacion": obtener_inflacion(),
        "cotizaciones": obtener_cotizaciones(),
        "actualizado": datetime.now().isoformat(),
    }
