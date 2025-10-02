"""
Validador de Resultados SQL - Sistema CFO Inteligente

Valida que los resultados de SQL sean razonables ANTES de generar narrativas.
Previene respuestas incorrectas causadas por SQL mal generado.

Reglas de negocio basadas en análisis de errores históricos.

Autor: Sistema CFO Inteligente
Versión: 1.0
Fecha: Octubre 2025
"""

from typing import Dict, Any, List, Optional
import re


class ValidadorSQL:
    """
    Valida resultados de queries SQL según reglas de negocio
    """
    
    # Límites razonables para Conexión Consultora
    LIMITES = {
        'distribucion_socio_max': 100_000,      # $ 100K por distribución individual
        'distribucion_socio_min': 0,
        'facturacion_mes_max': 10_000_000,      # $ 10M por mes
        'facturacion_dia_max': 1_000_000,       # $ 1M por día
        'gasto_mes_max': 5_000_000,             # $ 5M gastos/mes
        'gasto_dia_max': 500_000,               # $ 500K gastos/día
        'rentabilidad_min': -100,               # -100% a 100%
        'rentabilidad_max': 100,
        'porcentaje_min': 0,
        'porcentaje_max': 100,
        'tipo_cambio_min': 30,                  # UYU/USD razonable
        'tipo_cambio_max': 50,
        'retiro_max': 200_000,                  # $ 200K por retiro
    }
    
    @staticmethod
    def detectar_tipo_query(pregunta: str, sql: str) -> str:
        """
        Detecta qué tipo de query es para aplicar validaciones específicas
        
        Returns:
            'distribucion_socio' | 'rentabilidad' | 'facturacion' | 
            'gastos' | 'retiros' | 'porcentaje' | 'tipo_cambio' | 'general'
        """
        pregunta_lower = pregunta.lower()
        sql_upper = sql.upper()
        
        # Distribuciones por socio
        if any(nombre in pregunta_lower for nombre in ['bruno', 'agustina', 'viviana', 'gonzalo', 'pancho']):
            if 'distribu' in pregunta_lower or 'recib' in pregunta_lower or 'toca' in pregunta_lower:
                return 'distribucion_socio'
            if 'retir' in pregunta_lower:
                return 'retiros'
        
        # Rentabilidad
        if 'rentabilidad' in pregunta_lower or 'margen' in pregunta_lower:
            return 'rentabilidad'
        
        # Porcentajes
        if 'porcentaje' in pregunta_lower or '%%' in sql_upper or '* 100' in sql_upper:
            if 'rentabilidad' not in pregunta_lower:
                return 'porcentaje'
        
        # Facturación
        if 'factur' in pregunta_lower or 'ingreso' in pregunta_lower:
            if 'día' in pregunta_lower or 'hoy' in pregunta_lower:
                return 'facturacion_dia'
            return 'facturacion'
        
        # Gastos
        if 'gast' in pregunta_lower:
            if 'día' in pregunta_lower or 'hoy' in pregunta_lower:
                return 'gastos_dia'
            return 'gastos'
        
        # Retiros
        if 'retir' in pregunta_lower:
            return 'retiros'
        
        # Tipo de cambio
        if 'tipo de cambio' in pregunta_lower or 'cambio' in pregunta_lower:
            return 'tipo_cambio'
        
        return 'general'
    
    @classmethod
    def validar_rango(cls, valor: float, min_val: float, max_val: float, nombre: str) -> Dict[str, Any]:
        """Valida que un valor esté dentro de un rango razonable"""
        if valor is None:
            return {'valido': True, 'razon': None}
        
        if valor < min_val or valor > max_val:
            return {
                'valido': False,
                'razon': f'{nombre} fuera de rango razonable: {valor:,.2f} (esperado: {min_val:,.0f} - {max_val:,.0f})'
            }
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_distribucion_socio(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida distribuciones a socios"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': 'Sin distribuciones (válido)'}
        
        for row in resultado:
            # Buscar campos de monto
            for key in ['monto_uyu', 'monto_usd', 'total', 'total_uyu', 'total_usd']:
                if key in row and row[key] is not None:
                    monto = float(row[key])
                    if monto > cls.LIMITES['distribucion_socio_max']:
                        return {
                            'valido': False,
                            'razon': f'Distribución sospechosamente alta: ${monto:,.2f} (máx esperado: ${cls.LIMITES["distribucion_socio_max"]:,.0f})'
                        }
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_rentabilidad(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida rentabilidad (-100% a 100%)"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': 'Sin datos de rentabilidad'}
        
        for row in resultado:
            for key in ['rentabilidad', 'margen', 'margen_pct', 'rentabilidad_pct']:
                if key in row and row[key] is not None:
                    rentabilidad = float(row[key])
                    return cls.validar_rango(
                        rentabilidad,
                        cls.LIMITES['rentabilidad_min'],
                        cls.LIMITES['rentabilidad_max'],
                        'Rentabilidad'
                    )
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_porcentaje(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida porcentajes (0-100%)"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        # Sumar porcentajes para verificar que sumen ~100
        porcentajes = []
        
        for row in resultado:
            for key in ['porcentaje', 'pct', 'porcentaje_uyu', 'porcentaje_usd']:
                if key in row and row[key] is not None:
                    pct = float(row[key])
                    
                    # Validar rango individual
                    if pct < 0 or pct > 100:
                        return {
                            'valido': False,
                            'razon': f'Porcentaje fuera de rango: {pct:.2f}% (debe estar entre 0-100%)'
                        }
                    
                    porcentajes.append(pct)
        
        # Si hay múltiples porcentajes, verificar que sumen ~100
        if len(porcentajes) > 1:
            suma = sum(porcentajes)
            if abs(100 - suma) > 5:  # Tolerancia de 5%
                return {
                    'valido': False,
                    'razon': f'Porcentajes no suman 100%: suma={suma:.1f}% (esperado: ~100%)'
                }
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_facturacion(cls, resultado: List[Dict], es_dia: bool = False) -> Dict[str, Any]:
        """Valida facturación/ingresos"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        limite_max = cls.LIMITES['facturacion_dia_max'] if es_dia else cls.LIMITES['facturacion_mes_max']
        nombre = 'Facturación diaria' if es_dia else 'Facturación mensual'
        
        for row in resultado:
            for key in ['facturacion', 'ingresos', 'total', 'total_uyu', 'total_ingresos']:
                if key in row and row[key] is not None:
                    monto = float(row[key])
                    return cls.validar_rango(monto, 0, limite_max, nombre)
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_gastos(cls, resultado: List[Dict], es_dia: bool = False) -> Dict[str, Any]:
        """Valida gastos"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        limite_max = cls.LIMITES['gasto_dia_max'] if es_dia else cls.LIMITES['gasto_mes_max']
        nombre = 'Gastos diarios' if es_dia else 'Gastos mensuales'
        
        for row in resultado:
            for key in ['gastos', 'total_gastos', 'total', 'total_uyu', 'gasto']:
                if key in row and row[key] is not None:
                    monto = float(row[key])
                    return cls.validar_rango(monto, 0, limite_max, nombre)
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_retiros(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida retiros de socios"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        for row in resultado:
            for key in ['retiros', 'total_retiros', 'total', 'monto']:
                if key in row and row[key] is not None:
                    monto = float(row[key])
                    return cls.validar_rango(monto, 0, cls.LIMITES['retiro_max'], 'Retiro')
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_tipo_cambio(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida tipo de cambio UYU/USD"""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        for row in resultado:
            for key in ['tipo_cambio', 'tipo_cambio_promedio', 'promedio']:
                if key in row and row[key] is not None:
                    tc = float(row[key])
                    return cls.validar_rango(
                        tc,
                        cls.LIMITES['tipo_cambio_min'],
                        cls.LIMITES['tipo_cambio_max'],
                        'Tipo de cambio'
                    )
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_resultado(cls, pregunta: str, sql: str, resultado: List[Dict]) -> Dict[str, Any]:
        """
        Valida resultado de SQL según tipo de query
        
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
        tipo_query = cls.detectar_tipo_query(pregunta, sql)
        validaciones_aplicadas = []
        
        # Aplicar validaciones según tipo
        if tipo_query == 'distribucion_socio':
            validacion = cls.validar_distribucion_socio(resultado)
            validaciones_aplicadas.append('distribucion_socio')
            
        elif tipo_query == 'rentabilidad':
            validacion = cls.validar_rentabilidad(resultado)
            validaciones_aplicadas.append('rentabilidad')
            
        elif tipo_query == 'porcentaje':
            validacion = cls.validar_porcentaje(resultado)
            validaciones_aplicadas.append('porcentaje')
            
        elif tipo_query == 'facturacion':
            validacion = cls.validar_facturacion(resultado, es_dia=False)
            validaciones_aplicadas.append('facturacion_mes')
            
        elif tipo_query == 'facturacion_dia':
            validacion = cls.validar_facturacion(resultado, es_dia=True)
            validaciones_aplicadas.append('facturacion_dia')
            
        elif tipo_query == 'gastos':
            validacion = cls.validar_gastos(resultado, es_dia=False)
            validaciones_aplicadas.append('gastos_mes')
            
        elif tipo_query == 'gastos_dia':
            validacion = cls.validar_gastos(resultado, es_dia=True)
            validaciones_aplicadas.append('gastos_dia')
            
        elif tipo_query == 'retiros':
            validacion = cls.validar_retiros(resultado)
            validaciones_aplicadas.append('retiros')
            
        elif tipo_query == 'tipo_cambio':
            validacion = cls.validar_tipo_cambio(resultado)
            validaciones_aplicadas.append('tipo_cambio')
            
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
    Función wrapper para facilitar uso
    
    Uso:
        from app.services.validador_sql import validar_resultado_sql
        
        validacion = validar_resultado_sql(pregunta, sql, datos)
        if not validacion['valido']:
            # Resultado sospechoso, usar método alternativo
            pass
    """
    return ValidadorSQL.validar_resultado(pregunta, sql, resultado)


# ══════════════════════════════════════════════════════════════
# TESTING
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING VALIDADOR SQL")
    print("="*80)
    
    tests = [
        # Test 1: Distribución normal
        {
            'pregunta': '¿Cuánto recibió Bruno este año?',
            'sql': 'SELECT SUM(monto_uyu) as total FROM ...',
            'resultado': [{'total': 50000}],
            'esperado': True
        },
        # Test 2: Distribución sospechosamente alta
        {
            'pregunta': '¿Cuánto recibió Bruno este año?',
            'sql': 'SELECT SUM(monto_uyu) as total FROM ...',
            'resultado': [{'total': 500000}],  # $ 500K es demasiado
            'esperado': False
        },
        # Test 3: Rentabilidad normal
        {
            'pregunta': '¿Cuál es la rentabilidad?',
            'sql': 'SELECT rentabilidad FROM ...',
            'resultado': [{'rentabilidad': 33.47}],
            'esperado': True
        },
        # Test 4: Rentabilidad imposible
        {
            'pregunta': '¿Cuál es la rentabilidad?',
            'sql': 'SELECT rentabilidad FROM ...',
            'resultado': [{'rentabilidad': 250}],  # 250% imposible
            'esperado': False
        },
        # Test 5: Porcentajes que suman 100
        {
            'pregunta': '¿Qué porcentaje tiene cada área?',
            'sql': 'SELECT porcentaje FROM ...',
            'resultado': [
                {'area': 'Jurídica', 'porcentaje': 30},
                {'area': 'Notarial', 'porcentaje': 25},
                {'area': 'Contable', 'porcentaje': 45}
            ],
            'esperado': True
        },
        # Test 6: Porcentajes que NO suman 100
        {
            'pregunta': '¿Qué porcentaje tiene cada área?',
            'sql': 'SELECT porcentaje FROM ...',
            'resultado': [
                {'area': 'Jurídica', 'porcentaje': 30},
                {'area': 'Notarial', 'porcentaje': 80}
            ],
            'esperado': False
        },
    ]
    
    pasados = 0
    fallidos = 0
    
    for i, test in enumerate(tests, 1):
        validacion = ValidadorSQL.validar_resultado(
            test['pregunta'],
            test['sql'],
            test['resultado']
        )
        
        exito = validacion['valido'] == test['esperado']
        
        if exito:
            print(f"✅ Test {i}: {test['pregunta'][:40]}...")
            pasados += 1
        else:
            print(f"❌ Test {i}: {test['pregunta'][:40]}...")
            print(f"   Esperado: {test['esperado']}, Obtenido: {validacion['valido']}")
            print(f"   Razón: {validacion['razon']}")
            fallidos += 1
    
    print(f"\n{'='*80}")
    print(f"Resultado: {pasados}/{len(tests)} tests pasados")
    print("="*80)

