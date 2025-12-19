"""
Validador Canónico - Compara respuestas del CFO AI contra queries de control

Sistema de validación automática que:
- Identifica si una pregunta coincide con queries canónicas conocidas
- Ejecuta queries de control pre-validadas
- Compara resultados y genera advertencias si difieren >1%

Autor: Sistema CFO Inteligente
Versión: 2.0 (modular)
Fecha: Diciembre 2025
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional
import re

from app.core.logger import get_logger
from app.services.canonical_queries_config import QUERIES_CANONICAS

logger = get_logger(__name__)


class ValidadorCanonico:
    """
    Sistema de validación que compara respuestas del CFO AI 
    contra queries de control pre-definidas.
    
    Objetivo: Garantizar 99%+ de precisión en cifras financieras críticas.
    """
    
    # Re-exportar para compatibilidad
    QUERIES_CANONICAS = QUERIES_CANONICAS
    
    @classmethod
    def identificar_query_canonica(cls, pregunta: str) -> Optional[str]:
        """
        Identifica si la pregunta coincide con alguna query canónica.
        
        Args:
            pregunta: Pregunta del usuario
            
        Returns:
            Key de la query canónica o None si no coincide
        """
        pregunta_lower = pregunta.lower()
        
        for key, config in QUERIES_CANONICAS.items():
            for patron in config["patrones"]:
                if patron in pregunta_lower:
                    logger.debug(f"Query canónica identificada: {key} (patrón: '{patron}')")
                    return key
        
        return None
    
    @classmethod
    def ejecutar_query_control(cls, db: Session, query_key: str) -> Optional[float]:
        """
        Ejecuta la query de control y retorna el resultado.
        
        Args:
            db: Sesión de base de datos
            query_key: Key de la query canónica
            
        Returns:
            Valor numérico resultado o None si falla
        """
        if query_key not in QUERIES_CANONICAS:
            return None
        
        sql = QUERIES_CANONICAS[query_key]["sql_control"]
        
        try:
            result = db.execute(text(sql)).fetchone()
            if result and result[0] is not None:
                return float(result[0])
            return 0.0  # Si es NULL, retornar 0
        except Exception as e:
            logger.error(f"Error ejecutando query de control '{query_key}': {e}")
            return None
    
    @classmethod
    def extraer_valor_respuesta(cls, respuesta: str, datos_raw: Any) -> Optional[float]:
        """
        Extrae el valor numérico principal de la respuesta del CFO AI.
        
        Prioridad:
        1. datos_raw (más preciso)
        2. Texto de respuesta (regex)
        
        Args:
            respuesta: Texto de respuesta narrativa
            datos_raw: Datos crudos de la consulta SQL
            
        Returns:
            Valor numérico extraído o None
        """
        # 1. Intentar extraer de datos_raw primero (más preciso)
        valor = cls._extraer_de_datos_raw(datos_raw)
        if valor is not None:
            return valor
        
        # 2. Intentar extraer del texto de respuesta
        return cls._extraer_de_texto(respuesta)
    
    @classmethod
    def _extraer_de_datos_raw(cls, datos_raw: Any) -> Optional[float]:
        """Extrae valor numérico de datos_raw."""
        if not datos_raw:
            return None
        
        if isinstance(datos_raw, list) and len(datos_raw) > 0:
            primer_registro = datos_raw[0]
            if isinstance(primer_registro, dict):
                campos_prioritarios = [
                    'total', 'total_uyu', 'sum', 'monto', 'valor',
                    'rentabilidad', 'porcentaje', 'margen', 'ing', 'gas'
                ]
                for campo in campos_prioritarios:
                    if campo in primer_registro and primer_registro[campo] is not None:
                        try:
                            return float(primer_registro[campo])
                        except (ValueError, TypeError):
                            continue
        return None
    
    @classmethod
    def _extraer_de_texto(cls, respuesta: str) -> Optional[float]:
        """Extrae valor numérico del texto de respuesta usando regex."""
        patrones = [
            r'\$\s*([\d.,]+)',           # $12.340.660
            r'([\d.,]+)\s*%',            # 68,30%
            r'([\d.,]+)\s*UYU',          # 12340660 UYU
            r'([\d.,]+)\s*pesos',        # 12340660 pesos
            r'total[:\s]*([\d.,]+)',     # total: 12340660
        ]
        
        for patron in patrones:
            matches = re.findall(patron, respuesta, re.IGNORECASE)
            if matches:
                try:
                    valor_str = matches[0]
                    # Formato uruguayo: 1.234.567,89
                    if valor_str.count('.') > 1:
                        valor_str = valor_str.replace('.', '')
                    elif ',' in valor_str:
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                    return float(valor_str)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    @classmethod
    def validar_respuesta(
        cls, 
        db: Session, 
        pregunta: str, 
        respuesta: str, 
        datos_raw: Any = None
    ) -> Dict[str, Any]:
        """
        Valida la respuesta del CFO AI contra query de control.
        
        Args:
            db: Sesión de base de datos
            pregunta: Pregunta original del usuario
            respuesta: Respuesta narrativa del CFO AI
            datos_raw: Datos crudos de la consulta
            
        Returns:
            Dict con resultado de validación
        """
        resultado = cls._crear_resultado_vacio()
        
        # 1. Identificar query canónica
        query_key = cls.identificar_query_canonica(pregunta)
        if not query_key:
            return resultado
        
        resultado["query_canonica"] = query_key
        config = QUERIES_CANONICAS[query_key]
        
        # 2. Ejecutar query de control
        valor_control = cls.ejecutar_query_control(db, query_key)
        if valor_control is None:
            logger.warning(f"Validación canónica: No se pudo ejecutar query de control para '{query_key}'")
            return resultado
        
        resultado["valor_control"] = valor_control
        
        # 3. Extraer valor de respuesta CFO
        valor_cfo = cls.extraer_valor_respuesta(respuesta, datos_raw)
        if valor_cfo is None:
            logger.warning(f"Validación canónica: No se pudo extraer valor de respuesta CFO para '{query_key}'")
            return resultado
        
        resultado["valor_cfo"] = valor_cfo
        resultado["validado"] = True
        
        # 4. Calcular diferencia y verificar tolerancia
        diferencia = cls._calcular_diferencia(valor_cfo, valor_control)
        resultado["diferencia_porcentual"] = round(diferencia, 2)
        
        tolerancia_pct = config["tolerancia"] * 100
        resultado["dentro_tolerancia"] = diferencia <= tolerancia_pct
        
        # 5. Generar advertencia si fuera de tolerancia
        if not resultado["dentro_tolerancia"]:
            resultado["advertencia"] = cls._generar_advertencia(
                query_key, valor_cfo, valor_control, diferencia
            )
            logger.warning(
                f"Validación canónica FALLIDA [{query_key}]: "
                f"CFO=${valor_cfo:,.0f}, Control=${valor_control:,.0f}, "
                f"Diferencia={diferencia:.2f}% (tolerancia={tolerancia_pct}%)"
            )
        else:
            logger.info(
                f"Validación canónica OK [{query_key}]: "
                f"Diferencia={diferencia:.2f}% (tolerancia={tolerancia_pct}%)"
            )
        
        return resultado
    
    @staticmethod
    def _crear_resultado_vacio() -> Dict[str, Any]:
        """Crea estructura de resultado vacía."""
        return {
            "validado": False,
            "query_canonica": None,
            "valor_cfo": None,
            "valor_control": None,
            "diferencia_porcentual": None,
            "dentro_tolerancia": None,
            "advertencia": None
        }
    
    @staticmethod
    def _calcular_diferencia(valor_cfo: float, valor_control: float) -> float:
        """Calcula diferencia porcentual entre valores."""
        if valor_control != 0:
            return abs(valor_cfo - valor_control) / abs(valor_control) * 100
        return 0.0 if valor_cfo == 0 else 100.0
    
    @staticmethod
    def _generar_advertencia(query_key: str, valor_cfo: float, valor_control: float, diferencia: float) -> str:
        """Genera mensaje de advertencia para diferencias significativas."""
        return (
            f"\n\n⚠️ **ADVERTENCIA DE PRECISIÓN**: La respuesta difiere **{diferencia:.2f}%** "
            f"del valor de control.\n"
            f"- Valor reportado: ${valor_cfo:,.0f}\n"
            f"- Valor de control: ${valor_control:,.0f}\n"
            f"- Query de validación: `{query_key}`"
        )


# ══════════════════════════════════════════════════════════════
# FUNCIÓN DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════

def validar_respuesta_cfo(
    db: Session, 
    pregunta: str, 
    respuesta: str, 
    datos_raw: Any = None
) -> Dict[str, Any]:
    """
    Función wrapper para validar respuesta del CFO AI.
    
    Uso:
        from app.services.validador_canonico import validar_respuesta_cfo
        
        validacion = validar_respuesta_cfo(db, pregunta, respuesta, datos)
        if validacion.get('advertencia'):
            respuesta += validacion['advertencia']
    """
    return ValidadorCanonico.validar_respuesta(db, pregunta, respuesta, datos_raw)
