"""
SQL Result Validators - Valida resultados de queries según reglas de negocio.
Extraído de validador_sql.py para responsabilidad única.
"""
from typing import Dict, Any, List


class SQLResultValidators:
    """Validadores para diferentes tipos de resultados SQL."""
    
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
    
    @classmethod
    def validar_rango(cls, valor: float, min_val: float, max_val: float, nombre: str) -> Dict[str, Any]:
        """Valida que un valor esté dentro de un rango razonable."""
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
        """
        Valida distribuciones a socios.
        Solo valida que no sean negativos (sin límite máximo).
        """
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': 'Sin distribuciones (válido)'}
        
        for row in resultado:
            for key in ['monto_uyu', 'monto_usd', 'total', 'total_uyu', 'total_usd']:
                if key in row and row[key] is not None:
                    monto = float(row[key])
                    if monto < 0:
                        return {
                            'valido': False,
                            'razon': f'Distribución con valor negativo: ${monto:,.2f}'
                        }
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_rentabilidad(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida rentabilidad (-100% a 100%)."""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': 'Sin datos de rentabilidad'}
        
        for row in resultado:
            for key in ['rentabilidad', 'margen', 'margen_pct', 'rentabilidad_pct']:
                if key in row and row[key] is not None:
                    valor = str(row[key]).replace('%', '').strip()
                    rentabilidad = float(valor) if valor else 0.0
                    return cls.validar_rango(
                        rentabilidad,
                        cls.LIMITES['rentabilidad_min'],
                        cls.LIMITES['rentabilidad_max'],
                        'Rentabilidad'
                    )
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_porcentaje(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida porcentajes (0-100%) y que sumen ~100 si hay múltiples."""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        porcentajes = []
        
        for row in resultado:
            for key in ['porcentaje', 'pct', 'porcentaje_uyu', 'porcentaje_usd']:
                if key in row and row[key] is not None:
                    valor = str(row[key]).replace('%', '').strip()
                    pct = float(valor) if valor else 0.0
                    
                    if pct < 0 or pct > 100:
                        return {
                            'valido': False,
                            'razon': f'Porcentaje fuera de rango: {pct:.2f}% (debe estar entre 0-100%)'
                        }
                    
                    porcentajes.append(pct)
        
        # Verificar suma ~100 si hay múltiples porcentajes
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
        """Valida facturación/ingresos."""
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
        """Valida gastos."""
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
        """Valida retiros de socios (solo no negativos)."""
        if not resultado or len(resultado) == 0:
            return {'valido': True, 'razon': None}
        
        for row in resultado:
            for key in ['retiros', 'total_retiros', 'total', 'monto']:
                if key in row and row[key] is not None:
                    monto = float(row[key])
                    if monto < 0:
                        return {
                            'valido': False,
                            'razon': f'Retiro con valor negativo: ${monto:,.2f}'
                        }
        
        return {'valido': True, 'razon': None}
    
    @classmethod
    def validar_tipo_cambio(cls, resultado: List[Dict]) -> Dict[str, Any]:
        """Valida tipo de cambio UYU/USD (30-50)."""
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



