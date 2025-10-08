"""
Response Parser - Parsea respuestas de Claude

Parser robusto que maneja JSON válido, JSON con markdown, y texto plano.
Sin side effects, fácil de testear.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import json
import re
from typing import Dict, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


def parse_insights_response(response: str) -> Dict[str, str]:
    """
    Parsea respuesta de Claude a dict de insights.
    
    Maneja múltiples formatos:
    1. JSON válido directo: {"key": "value"}
    2. JSON en markdown: ```json\n{"key": "value"}\n```
    3. Texto plano: extrae secciones por patrones
    
    Args:
        response: String de respuesta de Claude
        
    Returns:
        Dict con insights parseados
        Si falla parsing, retorna dict con error
        
    Ejemplo:
        >>> response = '```json\\n{"insight_1": "Texto"}\\n```'
        >>> parse_insights_response(response)
        {'insight_1': 'Texto'}
    """
    if not response or not response.strip():
        logger.warning("Response vacía")
        return {"error": "Response vacía de Claude"}
    
    # INTENTO 1: JSON directo
    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict):
            logger.info(f"JSON parseado directamente: {len(parsed)} keys")
            return parsed
    except json.JSONDecodeError:
        pass
    
    # INTENTO 2: JSON en markdown (```json ... ```)
    json_match = re.search(
        r'```(?:json)?\s*\n(.*?)\n```',
        response,
        re.DOTALL | re.IGNORECASE
    )
    
    if json_match:
        json_str = json_match.group(1)
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                logger.info(f"JSON parseado desde markdown: {len(parsed)} keys")
                return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"JSON en markdown inválido: {e}")
    
    # INTENTO 3: Buscar JSON en cualquier parte del texto
    # A veces Claude envuelve JSON en texto explicativo
    try:
        # Buscar primer { y último }
        start = response.find('{')
        end = response.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = response[start:end]
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                logger.info(f"JSON encontrado en texto: {len(parsed)} keys")
                return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    
    # INTENTO 4: Parsear como texto plano (fallback)
    logger.warning("No se pudo parsear JSON, intentando extracción de texto")
    return _extract_insights_from_text(response)


def _extract_insights_from_text(text: str) -> Dict[str, str]:
    """
    Extrae insights de texto plano sin estructura JSON.
    
    Busca patrones como:
    - "Insight 1: ..."
    - "1. ..."
    - "- ..."
    
    Args:
        text: Texto plano de Claude
        
    Returns:
        Dict con insights extraídos
        Si no encuentra patrones, retorna el texto completo en "insight_1"
    """
    insights = {}
    
    # Patrón 1: "Insight N: texto" o "N. texto"
    pattern1 = re.compile(
        r'(?:insight[_\s]*|tendencia:|patrón:|oportunidad:|riesgo:|cambio[_\s]*principal:|evaluación:|recomendación:)?\s*(\d+)[\.:]\s*(.*?)(?=\n\s*\d+[\.:|\n\s*$])',
        re.IGNORECASE | re.DOTALL
    )
    
    matches = pattern1.findall(text)
    if matches:
        for i, (num, content) in enumerate(matches, 1):
            key = f"insight_{i}"
            insights[key] = content.strip()
        
        if insights:
            logger.info(f"Extraídos {len(insights)} insights de texto con patrón numérico")
            return insights
    
    # Patrón 2: Buscar keys específicos en texto
    # "Tendencia: ..." "Patrón: ..." etc
    specific_keys = [
        'tendencia', 'patron', 'patrón', 'oportunidad', 'riesgo',
        'cambio_principal', 'cambio principal', 'evaluacion', 'evaluación',
        'recomendacion', 'recomendación'
    ]
    
    for key in specific_keys:
        # Buscar "key: contenido" hasta siguiente key o fin
        pattern = re.compile(
            rf'{key}:\s*(.*?)(?={'|'.join(specific_keys)}:|\n\n|$)',
            re.IGNORECASE | re.DOTALL
        )
        match = pattern.search(text)
        if match:
            normalized_key = key.lower().replace('ó', 'o').replace('á', 'a').replace(' ', '_')
            insights[normalized_key] = match.group(1).strip()
    
    if insights:
        logger.info(f"Extraídos {len(insights)} insights de texto con keys específicos")
        return insights
    
    # Fallback final: retornar texto completo
    logger.warning("No se pudieron extraer insights estructurados, retornando texto completo")
    return {
        "insight_1": text[:500],  # Truncar a 500 chars
        "error": "No se pudo parsear estructura, texto truncado"
    }


def validate_insights(insights: Dict[str, str], required_keys: Optional[list] = None) -> bool:
    """
    Valida que insights tenga estructura mínima esperada.
    
    Args:
        insights: Dict parseado
        required_keys: Lista de keys requeridas (opcional)
        
    Returns:
        True si válido, False si no
    """
    if not insights or not isinstance(insights, dict):
        return False
    
    if required_keys:
        return all(key in insights for key in required_keys)
    
    # Validación mínima: al menos 1 key que no sea 'error'
    non_error_keys = [k for k in insights.keys() if k != 'error']
    return len(non_error_keys) >= 1


def clean_insight_text(text: str, max_length: int = 500) -> str:
    """
    Limpia texto de insight.
    
    Remueve:
    - Espacios múltiples
    - Saltos de línea múltiples
    - Caracteres especiales problemáticos
    
    Args:
        text: Texto a limpiar
        max_length: Máximo largo permitido
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
    
    # Remover múltiples espacios
    cleaned = re.sub(r'\s+', ' ', text)
    
    # Remover saltos de línea múltiples
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    
    # Truncar si es muy largo
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    
    return cleaned.strip()

