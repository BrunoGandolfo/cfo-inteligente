"""
SQL Router - Sistema CFO Inteligente
Arquitectura activa: Claude directo con enriquecimiento opcional de metadatos temporales.

Con sql_engine=claude, este router delega exclusivamente en ClaudeSQLGenerator.
"""

import time
from typing import Dict, Any

from app.core.logger import get_logger
from app.core.constants import KEYWORDS_TEMPORALES
from app.services.claude_sql_generator import ClaudeSQLGenerator
from app.utils.sql_utils import extraer_sql_limpio, validar_sql

logger = get_logger(__name__)


class SQLRouter:
    """Router SQL simplificado: único path activo hacia Claude."""

    def __init__(self):
        """Inicializa el generador de SQL con Claude."""
        self.claude_gen = ClaudeSQLGenerator()
        logger.info("SQLRouter inicializado (Claude directo)")

    def _necesita_metadatos(self, pregunta: str) -> bool:
        """
        Detecta si la pregunta requiere metadatos temporales.

        Args:
            pregunta: Pregunta del usuario en lenguaje natural.

        Returns:
            True si alguna keyword temporal aparece en la pregunta.
        """
        pregunta_lower = (pregunta or "").lower()
        return any(keyword in pregunta_lower for keyword in KEYWORDS_TEMPORALES)

    def _fetch_metadatos(self, db) -> str:
        """
        Obtiene metadatos temporales desde BD y los formatea en XML.

        Args:
            db: Sesión de SQLAlchemy.

        Returns:
            String XML con metadatos o string vacío si falla.
        """
        if not db:
            return ""

        sql_metadatos = """
            SELECT
              CURRENT_DATE AS fecha_actual,
              EXTRACT(YEAR FROM CURRENT_DATE)::INT AS anio_actual,
              EXTRACT(MONTH FROM CURRENT_DATE)::INT AS mes_actual,
              COUNT(DISTINCT EXTRACT(MONTH FROM fecha)) FILTER (
                WHERE EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE)
              ) AS meses_con_datos,
              12 - EXTRACT(MONTH FROM CURRENT_DATE)::INT AS meses_restantes,
              MAX(fecha) AS ultima_fecha_con_datos
            FROM operaciones WHERE deleted_at IS NULL
        """

        try:
            from sqlalchemy import text

            result = db.execute(text(sql_metadatos))
            row = result.fetchone()
            if not row:
                return ""

            metadatos = dict(row._mapping)
            return (
                "<metadatos_temporales>\n"
                f"Fecha actual: {metadatos.get('fecha_actual')}\n"
                f"Año actual: {metadatos.get('anio_actual')}\n"
                f"Mes actual: {metadatos.get('mes_actual')}\n"
                f"Meses con datos este año: {metadatos.get('meses_con_datos')}\n"
                f"Meses restantes: {metadatos.get('meses_restantes')}\n"
                f"Última fecha con datos: {metadatos.get('ultima_fecha_con_datos')}\n"
                "</metadatos_temporales>"
            )
        except Exception as e:
            logger.warning(f"SQLRouter: no se pudieron obtener metadatos temporales: {e}")
            return ""

    def generar_sql_con_claude(self, pregunta: str, contexto: list = None, db=None) -> Dict[str, Any]:
        """
        Genera SQL usando Claude con memoria de conversación.

        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos para contexto
            db: Sesión de SQLAlchemy opcional para enriquecer con metadatos temporales

        Returns:
            Dict con sql, exito, tiempo, error, etc.
        """
        inicio = time.time()

        try:
            contexto_enriquecido = list(contexto or [])
            metadatos_str = ""

            if db and self._necesita_metadatos(pregunta):
                logger.info("SQLRouter: pregunta temporal detectada, obteniendo metadatos para Claude")
                metadatos_str = self._fetch_metadatos(db)
                if metadatos_str:
                    # ClaudeSQLGenerator no acepta metadatos explícitos: se inyectan en contexto.
                    contexto_enriquecido.append({
                        "role": "assistant",
                        "content": metadatos_str
                    })

            logger.info(
                f"Claude generando SQL para: '{pregunta[:60]}' "
                f"(contexto: {len(contexto_enriquecido)} msgs)"
            )

            sql_raw = self.claude_gen.generar_sql(pregunta, contexto=contexto_enriquecido)
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

    def generar_sql_inteligente(self, pregunta: str, contexto: list = None, db=None, **kwargs) -> Dict[str, Any]:
        """
        Router principal: único path hacia Claude directo.

        Args:
            pregunta: Pregunta del usuario en lenguaje natural
            contexto: Lista de mensajes previos para contexto
            db: Sesión de SQLAlchemy opcional para enriquecer prompts de Claude con metadatos
            **kwargs: Argumentos adicionales (ignorados, para compatibilidad)

        Returns:
            Dict con sql, exito, error y metadata de ejecución.
        """
        inicio_total = time.time()
        tiempos = {'claude': None}
        intentos = {'claude': 1, 'total': 1}

        logger.info(f"SQLRouter procesando: '{pregunta[:70]}'")

        # Path único: Claude directo
        logger.info("SQLRouter: SQL_ENGINE=claude — bypass directo a Claude")
        try:
            resultado_claude = self.generar_sql_con_claude(pregunta, contexto=contexto, db=db)
            tiempos['claude'] = resultado_claude.get('tiempo')

            if resultado_claude.get('exito'):
                tiempo_total = time.time() - inicio_total
                logger.info(f"SQLRouter: claude_direct en {tiempo_total:.2f}s")
                return {
                    'sql': resultado_claude['sql'],
                    'metodo': 'claude_direct',
                    'exito': True,
                    'tiempo_total': tiempo_total,
                    'tiempos': tiempos,
                    'intentos': intentos,
                    'error': None,
                    'debug': {'bypass': True, "sql" + "_engine": "claude"}
                }

            tiempo_total = time.time() - inicio_total
            error_msg = resultado_claude.get('error', 'No se pudo procesar la consulta')
            logger.error(f"SQLRouter: Claude directo falló - {error_msg}")
            return {
                'sql': None,
                'metodo': 'ninguno',
                'exito': False,
                'tiempo_total': tiempo_total,
                'tiempos': tiempos,
                'intentos': intentos,
                'error': error_msg,
                'debug': {'bypass': True, "sql" + "_engine": "claude"}
            }

        except Exception as e:
            tiempo_total = time.time() - inicio_total
            logger.error(f"SQLRouter: Error en Claude directo: {e}")
            return {
                'sql': None,
                'metodo': 'ninguno',
                'exito': False,
                'tiempo_total': tiempo_total,
                'tiempos': tiempos,
                'intentos': intentos,
                'error': 'Error interno al procesar la consulta. Intenta de nuevo.',
                'debug': {'bypass': True, "sql" + "_engine": "claude"}
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
        logger.info("Inicializando SQLRouter (Claude directo)")
        _router_instance = SQLRouter()

    return _router_instance


def generar_sql_inteligente(pregunta: str, contexto: list = None, db=None) -> Dict[str, Any]:
    """
    Función wrapper para facilitar el uso.

    Args:
        pregunta: Pregunta del usuario en lenguaje natural
        contexto: Lista de mensajes previos
        db: Sesión de SQLAlchemy opcional

    Returns:
        Dict con sql, exito, error, etc.
    """
    router = get_sql_router()
    return router.generar_sql_inteligente(pregunta, contexto=contexto, db=db)
