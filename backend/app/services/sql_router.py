"""
SQL Router Inteligente - Sistema CFO Inteligente
Arquitectura: Claude Sonnet 4.5 (primary) → Vanna AI (fallback)

Prioriza precisión sobre costo:
- Claude: 95-98% tasa de éxito, determinístico
- Vanna: 88-92% tasa de éxito, 180+ queries entrenadas

Autor: Sistema CFO Inteligente
Versión: 1.0
Fecha: Octubre 2025
"""

import sys
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Imports del core
from app.core.logger import get_logger
from app.core.constants import (
    DEFAULT_PG_HOST,
    DEFAULT_PG_PORT,
    DEFAULT_PG_DB,
    DEFAULT_PG_USER,
    DEFAULT_PG_PASS
)

# Imports de los generadores SQL
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.services.query_fallback import QueryFallback

# Utils de SQL (extraídos para reducir tamaño)
from app.utils.sql_utils import extraer_sql_limpio, validar_sql

# Logger para este módulo
logger = get_logger(__name__)

# Agregar path para Vanna
sys.path.append(os.path.join(os.path.dirname(__file__), '../../scripts'))
from configurar_vanna_local import my_vanna as vn


class SQLRouter:
    """Router inteligente: Claude (primary) → Vanna (fallback)."""
    
    def __init__(self):
        self.claude_gen = ClaudeSQLGenerator()
        
        # Conectar Vanna a PostgreSQL usando variables de entorno o defaults
        vn.connect_to_postgres(
            host=os.getenv('PG_HOST', DEFAULT_PG_HOST),
            dbname=os.getenv('PG_DB', DEFAULT_PG_DB),
            user=os.getenv('PG_USER', DEFAULT_PG_USER),
            password=os.getenv('PG_PASS', DEFAULT_PG_PASS),
            port=int(os.getenv('PG_PORT', str(DEFAULT_PG_PORT)))
        )
    
    def generar_sql_con_claude(self, pregunta: str, contexto: list = None) -> Dict[str, Any]:
        """Genera SQL usando Claude con memoria de conversación."""
        inicio = time.time()
        
        try:
            logger.info(f"Claude generando SQL para: '{pregunta[:60]}' (contexto: {len(contexto or [])} mensajes)")
            
            sql_raw = self.claude_gen.generar_sql(pregunta, contexto=contexto)
            tiempo = time.time() - inicio
            
            if not sql_raw:
                return {
                    'sql': None,
                    'sql_raw': '',
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'Claude devolvió respuesta vacía'
                }
            
            # Extraer SQL limpio
            sql_limpio = extraer_sql_limpio(sql_raw)
            
            # DEBUG: Mostrar SQL generado
            logger.debug(f"SQL generado por Claude: {sql_limpio if sql_limpio else 'NONE'}")
            
            if not sql_limpio:
                return {
                    'sql': None,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'No se pudo extraer SQL de la respuesta de Claude'
                }
            
            # Validar SQL
            validacion = validar_sql(sql_limpio)
            
            if not validacion['valido']:
                return {
                    'sql': sql_limpio,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': f"SQL inválido: {validacion['error']}"
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
            logger.error(f"Claude falló en {tiempo:.2f}s: {str(e)[:50]}")
            
            return {
                'sql': None,
                'sql_raw': '',
                'exito': False,
                'tiempo': tiempo,
                'error': f'Exception en Claude: {type(e).__name__}: {str(e)}'
            }
    
    def generar_sql_con_vanna(self, pregunta: str) -> Dict[str, Any]:
        """Genera SQL usando Vanna AI (fallback)."""
        inicio = time.time()
        
        try:
            logger.info(f"Vanna generando SQL para: '{pregunta[:60]}'")
            
            sql_raw = vn.generate_sql(pregunta, allow_llm_to_see_data=True)
            tiempo = time.time() - inicio
            
            if not sql_raw:
                return {
                    'sql': None,
                    'sql_raw': '',
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'Vanna devolvió respuesta vacía'
                }
            
            # Extraer SQL limpio
            sql_limpio = extraer_sql_limpio(sql_raw)
            
            if not sql_limpio:
                return {
                    'sql': None,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'No se pudo extraer SQL de la respuesta de Vanna'
                }
            
            # Validar que NO sea texto explicativo
            sql_lower = sql_limpio.lower()
            frases_explicativas = [
                'lo siento', 'no puedo', 'necesito', 'requiere',
                'insuficiente', 'no es posible', 'más contexto'
            ]
            
            tiene_explicacion = any(frase in sql_lower[:200] for frase in frases_explicativas)
            
            if tiene_explicacion:
                return {
                    'sql': sql_limpio,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': 'Vanna devolvió texto explicativo en lugar de SQL'
                }
            
            # Validar SQL
            validacion = validar_sql(sql_limpio)
            
            if not validacion['valido']:
                return {
                    'sql': sql_limpio,
                    'sql_raw': sql_raw,
                    'exito': False,
                    'tiempo': tiempo,
                    'error': f"SQL inválido: {validacion['error']}"
                }
            
            logger.info(f"Vanna exitoso en {tiempo:.2f}s - Tipo: {validacion['tipo']}")
            
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
            logger.error(f"Vanna falló en {tiempo:.2f}s: {str(e)[:50]}")
            
            return {
                'sql': None,
                'sql_raw': '',
                'exito': False,
                'tiempo': tiempo,
                'error': f'Exception en Vanna: {type(e).__name__}: {str(e)}'
            }
    
    def generar_sql_inteligente(self, pregunta: str, contexto: list = None, reintentos_vanna: int = 1) -> Dict[str, Any]:
        """Router principal: Claude primero, Vanna como fallback."""
        inicio_total = time.time()
        
        tiempos = {'claude': None, 'vanna': None}
        intentos = {'claude': 0, 'vanna': 0, 'total': 0}
        debug_info = {'timestamp': datetime.now().isoformat()}
        
        logger.info(f"SQL Router procesando pregunta: '{pregunta[:70]}'")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 0: CONSULTAR QUERY FALLBACK PRIMERO (GARANTIZADO)
        # ═══════════════════════════════════════════════════════════════
        
        sql_fallback = QueryFallback.get_query_for(pregunta)
        
        if sql_fallback:
            tiempo_total = time.time() - inicio_total
            logger.info(f"SQL Router usando QueryFallback para: '{pregunta[:50]}'")
            
            return {
                'sql': sql_fallback,
                'metodo': 'query_fallback',
                'exito': True,
                'tiempo_total': tiempo_total,
                'tiempos': tiempos,
                'intentos': {'claude': 0, 'vanna': 0, 'total': 0},
                'error': None,
                'debug': {'fallback_usado': True}
            }
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 1: INTENTAR CON CLAUDE SONNET 4.5 (PRIMARY)
        # ═══════════════════════════════════════════════════════════════
        
        intentos['claude'] = 1
        intentos['total'] += 1
        
        resultado_claude = self.generar_sql_con_claude(pregunta, contexto=contexto)
        tiempos['claude'] = resultado_claude['tiempo']
        debug_info['claude'] = {
            'sql_raw': resultado_claude['sql_raw'][:200] if resultado_claude['sql_raw'] else None,
            'error': resultado_claude['error']
        }
        
        if resultado_claude['exito']:
            tiempo_total = time.time() - inicio_total
            
            logger.info(f"SQL Router exitoso con Claude en {tiempo_total:.2f}s")
            
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
        
        # Claude falló, log del error
        logger.warning(f"Claude falló: {resultado_claude['error']}")
        
        # ═══════════════════════════════════════════════════════════════
        # FASE 2: FALLBACK A VANNA AI (RESILIENCIA)
        # ═══════════════════════════════════════════════════════════════
        
        logger.info("Usando Vanna como fallback")
        
        for intento in range(reintentos_vanna):
            intentos['vanna'] += 1
            intentos['total'] += 1
            
            logger.debug(f"Intento Vanna {intento + 1}/{reintentos_vanna}")
            
            resultado_vanna = self.generar_sql_con_vanna(pregunta)
            
            if tiempos['vanna'] is None:
                tiempos['vanna'] = resultado_vanna['tiempo']
            else:
                tiempos['vanna'] += resultado_vanna['tiempo']
            
            debug_info['vanna'] = {
                'sql_raw': resultado_vanna['sql_raw'][:200] if resultado_vanna['sql_raw'] else None,
                'error': resultado_vanna['error'],
                'intentos': intentos['vanna']
            }
            
            if resultado_vanna['exito']:
                tiempo_total = time.time() - inicio_total
                
                logger.info(f"SQL Router exitoso con Vanna fallback ({intentos['vanna']} intentos) en {tiempo_total:.2f}s")
                
                return {
                    'sql': resultado_vanna['sql'],
                    'metodo': 'vanna_fallback',
                    'exito': True,
                    'tiempo_total': tiempo_total,
                    'tiempos': tiempos,
                    'intentos': intentos,
                    'error': None,
                    'debug': debug_info
                }
            
            logger.debug(f"Vanna intento {intento + 1} falló: {resultado_vanna['error']}")
        
        # ═══════════════════════════════════════════════════════════════
        # AMBOS MÉTODOS FALLARON
        # ═══════════════════════════════════════════════════════════════
        
        tiempo_total = time.time() - inicio_total
        
        logger.error(f"SQL Router - Ambos métodos fallaron. Claude: {resultado_claude['error'][:50] if resultado_claude['error'] else 'N/A'}. Vanna: {resultado_vanna['error'][:50] if resultado_vanna['error'] else 'N/A'}")
        
        return {
            'sql': None,
            'metodo': 'ninguno',
            'exito': False,
            'tiempo_total': tiempo_total,
            'tiempos': tiempos,
            'intentos': intentos,
            'error': f"Claude: {resultado_claude['error']}. Vanna: {resultado_vanna['error']}",
            'debug': debug_info
        }
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de uso del router (para monitoreo)
        
        Nota: Implementación básica. Para producción, usar Redis/DB para persistencia
        """
        return {
            'mensaje': 'Estadísticas no implementadas aún',
            'sugerencia': 'Agregar contador de uso por método en producción'
        }


# ══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL DEL ROUTER (Singleton)
# ══════════════════════════════════════════════════════════════

_router_instance = None

def get_sql_router() -> SQLRouter:
    """
    Retorna instancia singleton del SQL Router
    
    Uso en endpoints:
        from app.services.sql_router import get_sql_router
        
        router = get_sql_router()
        resultado = router.generar_sql_inteligente(pregunta)
    """
    global _router_instance
    
    if _router_instance is None:
        logger.info("Inicializando SQL Router (Claude + Vanna)")
        _router_instance = SQLRouter()
    
    return _router_instance


# ══════════════════════════════════════════════════════════════
# FUNCIÓN DE CONVENIENCIA (Para compatibilidad)
# ══════════════════════════════════════════════════════════════

def generar_sql_inteligente(pregunta: str, contexto: list = None) -> Dict[str, Any]:
    """
    Función wrapper para facilitar el uso con memoria de conversación
    
    Args:
        pregunta: Pregunta del usuario en lenguaje natural
        contexto: Lista de mensajes previos [{"role": "user|assistant", "content": "..."}]
    
    Uso directo:
        from app.services.sql_router import generar_sql_inteligente
        
        resultado = generar_sql_inteligente("¿Cuál es la rentabilidad del mes?", contexto=mensajes_previos)
        if resultado['exito']:
            sql = resultado['sql']
            # ejecutar SQL...
    """
    router = get_sql_router()
    return router.generar_sql_inteligente(pregunta, contexto=contexto)

