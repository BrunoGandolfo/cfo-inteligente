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
    MODIFICADO: Ahora el cache y valor por defecto usan PROMEDIO, no venta
    """
    # Verificar cache (válido por 24 horas)
    if _cache["valor"] and _cache["timestamp"]:
        if datetime.now() - _cache["timestamp"] < timedelta(hours=24):
            logger.info(f"Usando cache: {_cache['valor']} UYU ({_cache['fuente']})")
            return {
                "compra": _cache["valor"] - 0.5,  # Aproximación
                "venta": _cache["valor"] + 0.5,   # Aproximación
                "promedio": _cache["valor"],      # El cache guarda el promedio
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
            valor_compra = float(data.get("compra", 40.00))
            valor_venta = float(data.get("venta", 40.50))
            valor_promedio = (valor_compra + valor_venta) / 2

            # CAMBIO IMPORTANTE: Actualizar cache con PROMEDIO, no venta
            _cache["valor"] = valor_promedio
            _cache["timestamp"] = datetime.now()
            _cache["fuente"] = "DolarApi"

            logger.info(f"Tipo de cambio obtenido de DolarApi: Promedio={valor_promedio:.2f} (Compra={valor_compra}, Venta={valor_venta})")

            return {
                "compra": valor_compra,
                "venta": valor_venta,
                "promedio": valor_promedio,
                "fuente": "DolarApi",
                "actualizado": datetime.now().isoformat()
            }
    except Exception as e:
        logger.warning(f"Error obteniendo tipo de cambio de DolarApi: {e}")

    # Fallback: valor fijo de emergencia (usando promedio)
    valor_fallback = 40.25  # Promedio entre 40.00 y 40.50
    logger.warning(f"Usando valor fallback: {valor_fallback}")

    return {
        "compra": valor_fallback - 0.25,
        "venta": valor_fallback + 0.25,
        "promedio": valor_fallback,
        "fuente": "fallback",
        "actualizado": datetime.now().isoformat()
    }

def obtener_tipo_cambio_promedio() -> Dict[str, float]:
    """
    Nueva función que retorna específicamente el promedio
    """
    datos = obtener_tipo_cambio_actual()
    return {
        "valor": datos["promedio"],
        "fuente": datos["fuente"],
        "actualizado": datos["actualizado"]
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
