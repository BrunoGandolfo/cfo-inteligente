"""Servicio para obtener el tipo de cambio USD/UYU con cache y fallback."""

import logging
from datetime import datetime, timedelta
from typing import Dict

import requests

from app.core.constants import FALLBACK_COTIZACION_USD

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(hours=24)
DOLARAPI_TIMEOUT_SECONDS = 5
FALLBACK_TIPO_CAMBIO = FALLBACK_COTIZACION_USD

# Cache mejorado que guarda TODOS los valores
_cache = {
    "compra": None,
    "venta": None,
    "promedio": None,
    "timestamp": None,
    "fuente": None
}

def obtener_tipo_cambio_actual() -> Dict[str, float]:
    """
    Obtiene el tipo de cambio actual USD -> UYU
    Retorna compra, venta y promedio sin aproximaciones
    """
    # Verificar cache (válido por 24 horas)
    if _cache["promedio"] and _cache["timestamp"]:
        if datetime.now() - _cache["timestamp"] < CACHE_TTL:
            logger.info(f"Usando cache: Promedio={_cache['promedio']:.2f} UYU ({_cache['fuente']})")
            return {
                "compra": _cache["compra"],
                "venta": _cache["venta"],
                "promedio": _cache["promedio"],
                "fuente": _cache["fuente"],
                "actualizado": _cache["timestamp"].isoformat()
            }

    # Intentar obtener de DolarApi
    try:
        response = requests.get(
            "https://uy.dolarapi.com/v1/cotizaciones/usd",
            timeout=DOLARAPI_TIMEOUT_SECONDS
        )

        if response.status_code == 200:
            data = response.json()
            valor_compra = float(data.get("compra", FALLBACK_TIPO_CAMBIO["compra"]))
            valor_venta = float(data.get("venta", FALLBACK_TIPO_CAMBIO["venta"]))
            valor_promedio = (valor_compra + valor_venta) / 2

            # Guardar TODOS los valores en cache
            _cache["compra"] = valor_compra
            _cache["venta"] = valor_venta
            _cache["promedio"] = valor_promedio
            _cache["timestamp"] = datetime.now()
            _cache["fuente"] = "DolarApi"

            logger.info(f"Tipo de cambio de DolarApi: C={valor_compra}, V={valor_venta}, P={valor_promedio:.2f}")

            return {
                "compra": valor_compra,
                "venta": valor_venta,
                "promedio": valor_promedio,
                "fuente": "DolarApi",
                "actualizado": datetime.now().isoformat()
            }
    except Exception as e:
        logger.warning(f"Error obteniendo tipo de cambio de DolarApi: {e}")

    # Fallback: valores fijos de emergencia
    logger.warning("Usando valores fallback")
    
    return {
        **FALLBACK_TIPO_CAMBIO,
        "fuente": "fallback",
        "actualizado": datetime.now().isoformat()
    }
