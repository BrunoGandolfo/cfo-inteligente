"""
Router para búsqueda de legislación en IMPO.

Permite buscar leyes y decretos por número y año (opcional).
Si no se especifica año, busca desde 2025 hacia atrás.
Usa la API JSON pública de IMPO agregando ?json=true a cualquier URL.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import requests
import logging

from app.core.security import get_current_user
from app.models.usuario import Usuario

router = APIRouter(prefix="/api/impo", tags=["Legislación IMPO"])
logger = logging.getLogger(__name__)

IMPO_BASE_URL = "https://www.impo.com.uy/bases"
TIMEOUT_SEGUNDOS = 10


# ═══════════════════════════════════════════════════════════════
# FUNCIONES INTERNAS DE BÚSQUEDA
# ═══════════════════════════════════════════════════════════════

def _buscar_ley(numero: int, anio: int) -> dict:
    """
    Busca una ley específica por número y año.
    Retorna dict con datos o None si no existe.
    """
    try:
        url = f"{IMPO_BASE_URL}/leyes/{numero}-{anio}?json=true"
        response = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "tipo": "Ley",
                "numero": numero,
                "anio": anio,
                "titulo": data.get("titulo", f"Ley {numero}/{anio}"),
                "url": f"https://www.impo.com.uy/bases/leyes/{numero}-{anio}",
            }
    except requests.RequestException:
        pass
    
    return None


def _buscar_decreto(numero: int, anio: int) -> dict:
    """
    Busca un decreto específico por número y año.
    Retorna dict con datos o None si no existe.
    """
    try:
        url = f"{IMPO_BASE_URL}/decretos/{numero}-{anio}?json=true"
        response = requests.get(url, timeout=TIMEOUT_SEGUNDOS)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "tipo": "Decreto",
                "numero": numero,
                "anio": anio,
                "titulo": data.get("titulo", f"Decreto {numero}/{anio}"),
                "url": f"https://www.impo.com.uy/bases/decretos/{numero}-{anio}",
            }
    except requests.RequestException:
        pass
    
    return None


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS DE LEYES
# ═══════════════════════════════════════════════════════════════

@router.get("/ley/{numero}/{anio}")
def obtener_ley_con_anio(
    numero: int,
    anio: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una ley por número y año específico.
    Ejemplo: /api/impo/ley/17437/2001
    """
    logger.info(f"Buscando Ley {numero}/{anio}")
    resultado = _buscar_ley(numero, anio)
    
    if resultado:
        return resultado
    
    raise HTTPException(status_code=404, detail=f"Ley {numero}/{anio} no encontrada")


@router.get("/ley/{numero}")
def obtener_ley_sin_anio(
    numero: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una ley por número, buscando el año automáticamente.
    Busca desde 2025 hacia atrás hasta 1980.
    Ejemplo: /api/impo/ley/17437
    """
    logger.info(f"Buscando Ley {numero} (sin año, búsqueda automática)")
    
    # Probar desde 2025 hacia atrás
    for year in range(2025, 1979, -1):
        resultado = _buscar_ley(numero, year)
        if resultado:
            logger.info(f"Ley {numero} encontrada en año {year}")
            return resultado
    
    raise HTTPException(status_code=404, detail=f"Ley {numero} no encontrada")


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS DE DECRETOS
# ═══════════════════════════════════════════════════════════════

@router.get("/decreto/{numero}/{anio}")
def obtener_decreto_con_anio(
    numero: int,
    anio: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un decreto por número y año específico.
    Ejemplo: /api/impo/decreto/500/1991
    """
    logger.info(f"Buscando Decreto {numero}/{anio}")
    resultado = _buscar_decreto(numero, anio)
    
    if resultado:
        return resultado
    
    raise HTTPException(status_code=404, detail=f"Decreto {numero}/{anio} no encontrado")


@router.get("/decreto/{numero}")
def obtener_decreto_sin_anio(
    numero: int,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un decreto por número, buscando el año automáticamente.
    Busca desde 2025 hacia atrás hasta 1980.
    Ejemplo: /api/impo/decreto/500
    """
    logger.info(f"Buscando Decreto {numero} (sin año, búsqueda automática)")
    
    # Probar desde 2025 hacia atrás
    for year in range(2025, 1979, -1):
        resultado = _buscar_decreto(numero, year)
        if resultado:
            logger.info(f"Decreto {numero} encontrado en año {year}")
            return resultado
    
    raise HTTPException(status_code=404, detail=f"Decreto {numero} no encontrado")


# ═══════════════════════════════════════════════════════════════
# ENDPOINT GENÉRICO
# ═══════════════════════════════════════════════════════════════

@router.get("/buscar")
def buscar_norma(
    tipo: str,
    numero: int,
    anio: Optional[int] = None,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Endpoint genérico para buscar cualquier tipo de norma.
    
    Parámetros:
    - tipo: "ley" o "decreto"
    - numero: número de la norma
    - anio: año de la norma (opcional)
    """
    if tipo.lower() == "ley":
        if anio:
            return obtener_ley_con_anio(numero, anio, current_user)
        return obtener_ley_sin_anio(numero, current_user)
    elif tipo.lower() == "decreto":
        if anio:
            return obtener_decreto_con_anio(numero, anio, current_user)
        return obtener_decreto_sin_anio(numero, current_user)
    else:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'ley' o 'decreto'")
