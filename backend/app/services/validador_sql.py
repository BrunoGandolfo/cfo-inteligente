"""
Validador de Resultados SQL - Sistema CFO Inteligente

Valida que los resultados de SQL sean razonables ANTES de generar narrativas.
Previene respuestas incorrectas causadas por SQL mal generado.

Coordinador principal que delega a módulos especializados:
- validators/sql_type_detector: Detección de tipo de query
- validators/sql_result_validators: Validadores por tipo de resultado
- validators/sql_pre_validators: Validación pre-ejecución

Autor: Sistema CFO Inteligente
Versión: 2.0 (modular)
Fecha: Diciembre 2025
"""
from typing import Dict, Any, List

from app.services.validators.sql_type_detector import SQLTypeDetector
from app.services.validators.sql_result_validators import SQLResultValidators
from app.services.validators.sql_pre_validators import SQLPreValidators


class ValidadorSQL:
    """
    Valida resultados de queries SQL según reglas de negocio.
    Coordina entre módulos especializados de validación.
    """
    
    # Re-exportar constantes para compatibilidad
    LIMITES = SQLResultValidators.LIMITES
    
    # Re-exportar métodos de detección
    detectar_tipo_query = SQLTypeDetector.detectar_tipo_query
    _detectar_distribucion_socio = SQLTypeDetector._detectar_distribucion_socio
    _detectar_con_variante_dia = SQLTypeDetector._detectar_con_variante_dia
    
    # Re-exportar validadores de resultado
    validar_rango = SQLResultValidators.validar_rango
    validar_distribucion_socio = SQLResultValidators.validar_distribucion_socio
    validar_rentabilidad = SQLResultValidators.validar_rentabilidad
    validar_porcentaje = SQLResultValidators.validar_porcentaje
    validar_facturacion = SQLResultValidators.validar_facturacion
    validar_gastos = SQLResultValidators.validar_gastos
    validar_retiros = SQLResultValidators.validar_retiros
    validar_tipo_cambio = SQLResultValidators.validar_tipo_cambio
    
    # Re-exportar validadores pre-ejecución
    validar_sql_antes_ejecutar = SQLPreValidators.validar_sql_antes_ejecutar
    validar_sintaxis_basica = SQLPreValidators.validar_sintaxis_basica
    
    @classmethod
    def validar_resultado(cls, pregunta: str, sql: str, resultado: List[Dict]) -> Dict[str, Any]:
        """
        Valida resultado de SQL según tipo de query.
        
        Args:
            pregunta: Pregunta del usuario
            sql: SQL ejecutado
            resultado: Datos devueltos por PostgreSQL
            
        Returns:
            {
                'valido': bool,
                'razon': str o None,
                'tipo_query': str,
                'validaciones_aplicadas': list
            }
        """
        if not resultado:
            return {
                'valido': True,
                'razon': 'Resultado vacío (válido)',
                'tipo_query': 'vacio',
                'validaciones_aplicadas': []
            }
        
        # Detectar tipo de query
        tipo_query = SQLTypeDetector.detectar_tipo_query(pregunta, sql)
        validaciones_aplicadas = []
        
        # Mapa de tipo -> validador
        validadores = {
            'distribucion_socio': (SQLResultValidators.validar_distribucion_socio, 'distribucion_socio'),
            'rentabilidad': (SQLResultValidators.validar_rentabilidad, 'rentabilidad'),
            'porcentaje': (SQLResultValidators.validar_porcentaje, 'porcentaje'),
            'facturacion': (lambda r: SQLResultValidators.validar_facturacion(r, es_dia=False), 'facturacion_mes'),
            'facturacion_dia': (lambda r: SQLResultValidators.validar_facturacion(r, es_dia=True), 'facturacion_dia'),
            'gastos': (lambda r: SQLResultValidators.validar_gastos(r, es_dia=False), 'gastos_mes'),
            'gastos_dia': (lambda r: SQLResultValidators.validar_gastos(r, es_dia=True), 'gastos_dia'),
            'retiros': (SQLResultValidators.validar_retiros, 'retiros'),
            'tipo_cambio': (SQLResultValidators.validar_tipo_cambio, 'tipo_cambio'),
        }
        
        if tipo_query in validadores:
            validador_fn, nombre_validacion = validadores[tipo_query]
            validacion = validador_fn(resultado)
            validaciones_aplicadas.append(nombre_validacion)
        else:
            # Query general, sin validaciones específicas
            validacion = {'valido': True, 'razon': None}
            validaciones_aplicadas.append('general_sin_validacion')
        
        return {
            'valido': validacion['valido'],
            'razon': validacion['razon'],
            'tipo_query': tipo_query,
            'validaciones_aplicadas': validaciones_aplicadas
        }


# ══════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════

def validar_resultado_sql(pregunta: str, sql: str, resultado: List[Dict]) -> Dict[str, Any]:
    """
    Función wrapper para facilitar uso.
    
    Uso:
        from app.services.validador_sql import validar_resultado_sql
        
        validacion = validar_resultado_sql(pregunta, sql, datos)
        if not validacion['valido']:
            # Resultado sospechoso, usar método alternativo
            pass
    """
    return ValidadorSQL.validar_resultado(pregunta, sql, resultado)
