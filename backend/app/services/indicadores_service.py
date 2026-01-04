"""
Servicio de Indicadores Económicos de Uruguay.

Indicadores con valores actualizables manualmente:
- UI (Unidad Indexada): actualización diaria
- UR (Unidad Reajustable): actualización mensual
- IPC (Índice de Precios): actualización mensual
- BPC (Base Prestaciones): actualización anual

Cotizaciones con API en tiempo real:
- USD/EUR/BRL: DolarApi

TODO: Integrar con API del INE cuando esté disponible.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

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

# Fallback para cotizaciones si falla DolarApi
COTIZACIONES_FALLBACK = {
    "usd_compra": 43.50,
    "usd_venta": 44.50,
    "eur_compra": 45.80,
    "eur_venta": 46.80,
    "brl_compra": 7.00,
    "brl_venta": 7.20,
}

# ═══════════════════════════════════════════════════════════════
# CACHE PARA COTIZACIONES (las únicas que se obtienen en tiempo real)
# ═══════════════════════════════════════════════════════════════

_cache_cotizaciones: Dict[str, Any] = {
    "data": None,
    "timestamp": None,
}

TTL_COTIZACIONES_HORAS = 1  # Refrescar cada hora


def _cache_cotizaciones_valido() -> bool:
    """Verifica si el cache de cotizaciones está vigente."""
    if not _cache_cotizaciones["timestamp"]:
        return False
    return datetime.now() - _cache_cotizaciones["timestamp"] < timedelta(hours=TTL_COTIZACIONES_HORAS)


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

def _obtener_cotizacion_moneda(moneda: str) -> Dict[str, float]:
    """
    Obtiene cotización de una moneda desde DolarApi.
    
    Args:
        moneda: Código de moneda (usd, eur, brl)
        
    Returns:
        Dict con compra y venta
    """
    fallback_compra = COTIZACIONES_FALLBACK[f"{moneda}_compra"]
    fallback_venta = COTIZACIONES_FALLBACK[f"{moneda}_venta"]
    
    try:
        response = requests.get(
            f"https://uy.dolarapi.com/v1/cotizaciones/{moneda}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "compra": float(data.get("compra", fallback_compra)),
                "venta": float(data.get("venta", fallback_venta)),
            }
    except Exception as e:
        logger.warning(f"Error obteniendo cotización de {moneda}: {e}")
    
    return {
        "compra": fallback_compra,
        "venta": fallback_venta,
    }


def obtener_cotizaciones() -> Dict[str, Any]:
    """
    Obtiene todas las cotizaciones de monedas (USD, EUR, BRL).
    
    Fuente: DolarApi (https://uy.dolarapi.com)
    Cache: 1 hora
    """
    global _cache_cotizaciones
    
    # Verificar cache
    if _cache_cotizaciones_valido() and _cache_cotizaciones["data"]:
        logger.info("Cotizaciones desde cache")
        return _cache_cotizaciones["data"]
    
    # Obtener cotizaciones
    cotizaciones = {
        "usd": _obtener_cotizacion_moneda("usd"),
        "eur": _obtener_cotizacion_moneda("eur"),
        "brl": _obtener_cotizacion_moneda("brl"),
        "timestamp": datetime.now().isoformat(),
    }
    
    # Guardar en cache
    _cache_cotizaciones = {
        "data": cotizaciones,
        "timestamp": datetime.now(),
    }
    
    logger.info("Cotizaciones obtenidas de DolarApi")
    return cotizaciones


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
