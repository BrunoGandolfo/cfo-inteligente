"""
SQL Router - Sistema CFO Inteligente
Arquitectura: Claude Sonnet 4 (único proveedor)

Si Claude falla, usa QueryFallback (queries predefinidas).
Si ambos fallan, retorna error claro al usuario.

Autor: Sistema CFO Inteligente
Versión: 2.0 (Simplificado - Solo Claude)
Fecha: Diciembre 2025
"""

import time
from typing import Dict, Any
from datetime import datetime

from app.core.logger import get_logger
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.services.query_fallback import QueryFallback
from app.utils.sql_utils import extraer_sql_limpio, validar_sql

logger = get_logger(__name__)


class SQLRouter:
    """
    Router de SQL simplificado: Claude → QueryFallback.
    
    Flujo:
    1. Buscar en QueryFallback (queries predefinidas optimizadas)
    2. Si no hay match, usar Claude para generar SQL
    3. Si Claude falla, retornar error claro
    """
    
    def __init__(self):
        """Inicializa el generador de SQL con Claude."""
        self.claude_gen = ClaudeSQLGenerator()
        logger.info("SQLRouter inicializado (Claude único proveedor)")
    
    def generar_sql_con_claude(self, pregunta: str, contexto: list = None) -> Dict[str, Any]:
        """
        Genera SQL usando Claude con memoria de conversación.
        
        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos para contexto
            
        Returns:
            Dict con sql, exito, tiempo, error, etc.
        """
        inicio = time.time()
        
        try:
            logger.info(f"Claude generando SQL para: '{pregunta[:60]}' (contexto: {len(contexto or [])} msgs)")
            
            sql_raw = self.claude_gen.generar_sql(pregunta, contexto=contexto)
            tiempo = time.time() - inicio
            
            if not sql_raw:
                return {
                    'sql': None,
                    'sql_raw': '',
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'Claude no pudo generar una respuesta. Por favor, intenta de nuevo.'
                }
            
            # Verificar si es un mensaje de error del orchestrator
            if sql_raw.startswith("ERROR:"):
                return {
                    'sql': None,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'El servicio de IA no está disponible temporalmente. Intenta en unos minutos.'
                }
            
            # Extraer SQL limpio
            sql_limpio = extraer_sql_limpio(sql_raw)
            
            logger.debug(f"SQL raw: {sql_raw[:200] if sql_raw else 'NONE'}")
            logger.debug(f"SQL limpio: {sql_limpio[:200] if sql_limpio else 'NONE'}")
            
            if not sql_limpio:
                # Claude respondió pero no con SQL válido
                return {
                    'sql': None,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'No pude entender la consulta. ¿Podrías reformularla de otra manera?'
                }
            
            # Validar SQL
            validacion = validar_sql(sql_limpio)
            
            if not validacion['valido']:
                return {
                    'sql': sql_limpio,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': f"El SQL generado tiene un problema: {validacion['error']}"
                }
            
            logger.info(f"Claude exitoso en {tiempo:.2f}s - Tipo: {validacion['tipo']}")
            
            return {
                'sql': sql_limpio,
                'sql_raw': sql_raw,
                'exito': True,
                'tiempo': tiempo,
                'error': None,
                'validacion': validacion
            }
        
        except Exception as e:
            tiempo = time.time() - inicio
            logger.error(f"Claude falló en {tiempo:.2f}s: {str(e)[:100]}", exc_info=True)
            
            return {
                'sql': None,
                'sql_raw': '',
                'exito': False,
                'tiempo': tiempo,
                'error': 'Error interno al procesar la consulta. Intenta de nuevo.'
            }
    
    def generar_sql_inteligente(self, pregunta: str, contexto: list = None, **kwargs) -> Dict[str, Any]:
        """
        Router principal: QueryFallback → Claude.
        
        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos para contexto
            **kwargs: Argumentos adicionales (ignorados, para compatibilidad)
            
        Returns:
            Dict con:
            - sql: Query SQL generada o None
            - metodo: 'query_fallback' | 'claude' | 'ninguno'
            - exito: True si se generó SQL válido
            - tiempo_total: Tiempo total en segundos
            - tiempos: Dict con tiempos por método
            - intentos: Dict con conteo de intentos
            - error: Mensaje de error o None
        """
        inicio_total = time.time()
        
        tiempos = {'claude': None, 'fallback': None}
        intentos = {'claude': 0, 'fallback': 0, 'total': 0}
        debug_info = {'timestamp': datetime.now().isoformat()}
        
        logger.info(f"SQLRouter procesando: '{pregunta[:70]}'")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 1: CONSULTAR QUERY FALLBACK (QUERIES PREDEFINIDAS)
        # ═══════════════════════════════════════════════════════════════
        
        inicio_fallback = time.time()
        sql_fallback = QueryFallback.get_query_for(pregunta)
        tiempos['fallback'] = time.time() - inicio_fallback
        intentos['fallback'] = 1
        intentos['total'] += 1
        
        if sql_fallback:
            tiempo_total = time.time() - inicio_total
            logger.info(f"SQLRouter: QueryFallback encontró match en {tiempo_total:.3f}s")
            
            return {
                'sql': sql_fallback,
                'metodo': 'query_fallback',
                'exito': True,
                'tiempo_total': tiempo_total,
                'tiempos': tiempos,
                'intentos': intentos,
                'error': None,
                'debug': {'fallback_usado': True}
            }
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 2: GENERAR CON CLAUDE
        # ═══════════════════════════════════════════════════════════════
        
        intentos['claude'] = 1
        intentos['total'] += 1
        
        resultado_claude = self.generar_sql_con_claude(pregunta, contexto=contexto)
        tiempos['claude'] = resultado_claude['tiempo']
        
        debug_info['claude'] = {
            'sql_raw_preview': resultado_claude.get('sql_raw', '')[:200] if resultado_claude.get('sql_raw') else None,
            'error': resultado_claude.get('error')
        }
        
        if resultado_claude['exito']:
            tiempo_total = time.time() - inicio_total
            logger.info(f"SQLRouter: Claude exitoso en {tiempo_total:.2f}s")
            
            return {
                'sql': resultado_claude['sql'],
                'metodo': 'claude',
                'exito': True,
                'tiempo_total': tiempo_total,
                'tiempos': tiempos,
                'intentos': intentos,
                'error': None,
                'debug': debug_info
            }
        
        # ═══════════════════════════════════════════════════════════════
        # CLAUDE FALLÓ - RETORNAR ERROR CLARO
        # ═══════════════════════════════════════════════════════════════
        
        tiempo_total = time.time() - inicio_total
        error_msg = resultado_claude.get('error', 'No se pudo procesar la consulta')
        
        logger.error(f"SQLRouter: Claude falló - {error_msg}")
        
        return {
            'sql': None,
            'metodo': 'ninguno',
            'exito': False,
            'tiempo_total': tiempo_total,
            'tiempos': tiempos,
            'intentos': intentos,
            'error': error_msg,
            'debug': debug_info
        }
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Retorna estadísticas del router (para monitoreo)."""
        return {
            'proveedor': 'claude',
            'modelo': 'claude-sonnet-4-20250514',
            'fallback': 'query_fallback',
            'mensaje': 'Sistema simplificado - Solo Claude'
        }


# ══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL DEL ROUTER (Singleton)
# ══════════════════════════════════════════════════════════════

_router_instance = None


def get_sql_router() -> SQLRouter:
    """
    Retorna instancia singleton del SQL Router.
    
    Uso:
        from app.services.sql_router import get_sql_router
        
        router = get_sql_router()
        resultado = router.generar_sql_inteligente(pregunta)
    """
    global _router_instance
    
    if _router_instance is None:
        logger.info("Inicializando SQLRouter (Claude único)")
        _router_instance = SQLRouter()
    
    return _router_instance


def generar_sql_inteligente(pregunta: str, contexto: list = None) -> Dict[str, Any]:
    """
    Función wrapper para facilitar el uso.
    
    Args:
        pregunta: Pregunta del usuario en lenguaje natural
        contexto: Lista de mensajes previos
        
    Returns:
        Dict con sql, exito, error, etc.
    """
    router = get_sql_router()
    return router.generar_sql_inteligente(pregunta, contexto=contexto)
