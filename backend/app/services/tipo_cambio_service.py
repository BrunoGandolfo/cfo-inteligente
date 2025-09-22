import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Cache simple en memoria
_cache = {
    "valor": None,
    "timestamp": None,
    "fuente": None
}

def obtener_tipo_cambio_actual() -> Dict[str, float]:
    """
    Obtiene el tipo de cambio actual USD -> UYU
    Prioridad: 1) Cache, 2) DolarApi, 3) Valor fallback
    """
    # Verificar cache (válido por 24 horas)
    if _cache["valor"] and _cache["timestamp"]:
        if datetime.now() - _cache["timestamp"] < timedelta(hours=24):
            logger.info(f"Usando cache: {_cache['valor']} UYU ({_cache['fuente']})")
            return {
                "compra": _cache["valor"] - 0.5,  # Aproximación
                "venta": _cache["valor"],
                "promedio": _cache["valor"] - 0.25,
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
            # DolarApi retorna compra y venta
            valor_venta = float(data.get("venta", 40.50))
            
            # Actualizar cache
            _cache["valor"] = valor_venta
            _cache["timestamp"] = datetime.now()
            _cache["fuente"] = "DolarApi"
            
            logger.info(f"Tipo de cambio obtenido de DolarApi: {valor_venta}")
            
            return {
                "compra": float(data.get("compra", valor_venta - 0.5)),
                "venta": valor_venta,
                "promedio": (float(data.get("compra", valor_venta - 0.5)) + valor_venta) / 2,
                "fuente": "DolarApi",
                "actualizado": datetime.now().isoformat()
            }
    except Exception as e:
        logger.warning(f"Error obteniendo tipo de cambio de DolarApi: {e}")
    
    # Fallback: valor fijo de emergencia
    valor_fallback = 40.50  # Actualizar manualmente si es necesario
    logger.warning(f"Usando valor fallback: {valor_fallback}")
    
    return {
        "compra": valor_fallback - 0.5,
        "venta": valor_fallback,
        "promedio": valor_fallback - 0.25,
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
    pass
