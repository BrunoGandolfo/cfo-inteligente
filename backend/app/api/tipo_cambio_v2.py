from fastapi import APIRouter
from app.services.tipo_cambio_service import obtener_tipo_cambio_actual

router = APIRouter()

@router.get("/hoy")
def obtener_tipo_cambio_hoy():
    """
    Obtiene el tipo de cambio del día USD -> UYU
    Retorna compra, venta, promedio y fuente
    """
    return obtener_tipo_cambio_actual()

@router.get("/venta")
def obtener_tipo_cambio_venta():
    """
    Obtiene solo el tipo de cambio de venta (el más usado)
    """
    datos = obtener_tipo_cambio_actual()
    return {
        "valor": datos["venta"],
        "fuente": datos["fuente"],
        "actualizado": datos["actualizado"]
    }

@router.get("/promedio")
def obtener_tipo_cambio_promedio():
    """
    Obtiene el tipo de cambio PROMEDIO entre compra y venta
    Este es el valor más justo para conversiones
    """
    datos = obtener_tipo_cambio_actual()
    return {
        "valor": datos["promedio"],
        "fuente": datos["fuente"],
        "actualizado": datos["actualizado"],
        "detalle": {
            "compra": datos["compra"],
            "venta": datos["venta"],
            "promedio": datos["promedio"]
        }
    }
