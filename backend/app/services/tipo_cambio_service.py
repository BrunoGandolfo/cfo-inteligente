import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

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
        if datetime.now() - _cache["timestamp"] < timedelta(hours=24):
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
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            valor_compra = float(data.get("compra", 40.00))
            valor_venta = float(data.get("venta", 40.50))
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
        "compra": 40.00,
        "venta": 40.50,
        "promedio": 40.25,
        "fuente": "fallback",
        "actualizado": datetime.now().isoformat()
    }

# TODO: Implementar función para BCU SOAP cuando se requiera fuente oficial
def obtener_tipo_cambio_bcu() -> Optional[float]:
    """
    Futura implementación con BCU SOAP
    Código de referencia en comentarios
    """
    # Ver investigación: código 2225 para USD billete
    # Endpoint: https://cotizaciones.bcu.gub.uy/wscotizaciones/servlet/awsbcucotizaciones
