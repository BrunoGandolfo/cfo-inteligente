"""
Router para búsqueda de legislación en IMPO.

Permite buscar leyes y decretos por número y año.
Usa la API JSON pública de IMPO agregando ?json=true a cualquier URL.
"""

from fastapi import APIRouter, Depends, HTTPException
import requests
import logging

from app.core.security import get_current_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/impo", tags=["Legislación IMPO"])
logger = logging.getLogger(__name__)

IMPO_BASE_URL = "https://www.impo.com.uy/bases"
TIMEOUT_SEGUNDOS = 10


@router.get("/ley/{numero}/{anio}")
def obtener_ley(
    numero: int,
    anio: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el texto de una ley por número y año.
    
    Ejemplo: /api/impo/ley/17437/2001
    """
    try:
        url = f"{IMPO_BASE_URL}/leyes/{numero}-{anio}?json=true"
        logger.info(f"Consultando IMPO: {url}")
        
        response = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "tipo": "Ley",
                "numero": numero,
                "anio": anio,
                "titulo": data.get("titulo", f"Ley {numero}/{anio}"),
                "texto": data.get("texto", data.get("contenido", "")),
                "url": f"https://www.impo.com.uy/bases/leyes/{numero}-{anio}",
                "datos": data,
            }
        else:
            logger.warning(f"Ley no encontrada: {numero}/{anio} - Status: {response.status_code}")
            raise HTTPException(status_code=404, detail=f"Ley {numero}/{anio} no encontrada")
            
    except requests.RequestException as e:
        logger.error(f"Error consultando IMPO: {e}")
        raise HTTPException(status_code=503, detail="Error conectando con IMPO")


@router.get("/decreto/{numero}/{anio}")
def obtener_decreto(
    numero: int,
    anio: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el texto de un decreto por número y año.
    
    Ejemplo: /api/impo/decreto/500/1991
    """
    try:
        url = f"{IMPO_BASE_URL}/decretos/{numero}-{anio}?json=true"
        logger.info(f"Consultando IMPO: {url}")
        
        response = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "tipo": "Decreto",
                "numero": numero,
                "anio": anio,
                "titulo": data.get("titulo", f"Decreto {numero}/{anio}"),
                "texto": data.get("texto", data.get("contenido", "")),
                "url": f"https://www.impo.com.uy/bases/decretos/{numero}-{anio}",
                "datos": data,
            }
        else:
            logger.warning(f"Decreto no encontrado: {numero}/{anio} - Status: {response.status_code}")
            raise HTTPException(status_code=404, detail=f"Decreto {numero}/{anio} no encontrado")
            
    except requests.RequestException as e:
        logger.error(f"Error consultando IMPO: {e}")
        raise HTTPException(status_code=503, detail="Error conectando con IMPO")


@router.get("/buscar")
def buscar_norma(
    tipo: str,
    numero: int,
    anio: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint genérico para buscar cualquier tipo de norma.
    
    Parámetros:
    - tipo: "ley" o "decreto"
    - numero: número de la norma
    - anio: año de la norma
    """
    if tipo.lower() == "ley":
        return obtener_ley(numero, anio, current_user)
    elif tipo.lower() == "decreto":
        return obtener_decreto(numero, anio, current_user)
    else:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'ley' o 'decreto'")
