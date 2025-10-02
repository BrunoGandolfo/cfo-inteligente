"""
Suite de Tests para ValidadorSQL - Sistema CFO Inteligente

Tests exhaustivos de validación de resultados SQL sin dependencias externas.
Cubre todos los métodos de la clase ValidadorSQL.

Ejecutar:
    cd backend
    pytest tests/test_validador_sql.py -v
    pytest tests/test_validador_sql.py -v --cov=app.services.validador_sql

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import pytest
from app.services.validador_sql import ValidadorSQL, validar_resultado_sql


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE DISTRIBUCIONES POR SOCIO
# ══════════════════════════════════════════════════════════════

class TestDistribucionesSocio:
    """Tests de validación de distribuciones a socios"""
    
    @pytest.mark.parametrize("monto,esperado", [
        (10_000, True),      # $10K - normal
        (50_000, True),      # $50K - normal alto
        (99_999, True),      # $99K - en el límite
        (0, True),           # $0 - sin distribución
        (500, True),         # $500 - muy bajo pero válido
    ])
    def test_distribucion_socio_valida(self, monto, esperado):
        """
        Arrange: Distribucion con monto válido
        Act: Validar distribución
        Assert: Debe ser válida
        """
        # Arrange
        resultado = [{'monto_uyu': monto}]
        
        # Act
        validacion = ValidadorSQL.validar_distribucion_socio(resultado)
        
        # Assert
        assert validacion['valido'] == esperado
        assert validacion['razon'] is None or 'Sin distribuciones' in validacion['razon']
    
    @pytest.mark.parametrize("monto,debe_fallar", [
        (-1000, True),       # Negativo - inválido
        (-50_000, True),     # Muy negativo
    ])
    def test_distribucion_socio_invalida(self, monto, debe_fallar):
        """
        Arrange: Distribución con valor negativo
        Act: Validar
        Assert: Debe rechazar valores negativos
        """
        # Arrange
        resultado = [{'total_uyu': monto}]
        
        # Act
        validacion = ValidadorSQL.validar_distribucion_socio(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'negativo' in validacion['razon']
    
    def test_distribucion_socio_vacia(self):
        """Resultado vacío debe ser válido"""
        # Arrange
        resultado = []
        
        # Act
        validacion = ValidadorSQL.validar_distribucion_socio(resultado)
        
        # Assert
        assert validacion['valido'] is True
        assert 'Sin distribuciones' in validacion['razon']
    
    def test_distribucion_socio_multiples_campos(self):
        """Debe validar cualquier campo de monto"""
        # Arrange
        resultado = [{'monto_usd': -5000}]  # Negativo en campo diferente
        
        # Act
        validacion = ValidadorSQL.validar_distribucion_socio(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'negativo' in validacion['razon']


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE RENTABILIDAD
# ══════════════════════════════════════════════════════════════

class TestRentabilidad:
    """Tests de validación de rentabilidad"""
    
    @pytest.mark.parametrize("rentabilidad,esperado", [
        (0, True),           # 0% - punto de equilibrio
        (33.47, True),       # 33% - normal
        (75.5, True),        # 75% - excelente
        (100, True),         # 100% - máximo teórico
        (-50, True),         # -50% - pérdida válida
        (-100, True),        # -100% - límite inferior
    ])
    def test_rentabilidad_valida(self, rentabilidad, esperado):
        """
        Arrange: Rentabilidad dentro de rango -100 a 100
        Act: Validar
        Assert: Debe ser válida
        """
        # Arrange
        resultado = [{'rentabilidad': rentabilidad}]
        
        # Act
        validacion = ValidadorSQL.validar_rentabilidad(resultado)
        
        # Assert
        assert validacion['valido'] == esperado
    
    @pytest.mark.parametrize("rentabilidad,debe_fallar", [
        (101, True),         # Apenas sobre 100%
        (250, True),         # Muy alto
        (-101, True),        # Bajo -100%
        (-500, True),        # Extremadamente negativo
    ])
    def test_rentabilidad_invalida(self, rentabilidad, debe_fallar):
        """
        Arrange: Rentabilidad fuera de rango razonable
        Act: Validar
        Assert: Debe rechazar
        """
        # Arrange
        resultado = [{'rentabilidad': rentabilidad}]
        
        # Act
        validacion = ValidadorSQL.validar_rentabilidad(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'fuera de rango' in validacion['razon']
    
    def test_rentabilidad_diferentes_nombres_campo(self):
        """Debe reconocer diferentes nombres de campo de rentabilidad"""
        # Arrange & Act & Assert
        campos = ['rentabilidad', 'margen', 'margen_pct', 'rentabilidad_pct']
        
        for campo in campos:
            resultado = [{campo: 50.5}]
            validacion = ValidadorSQL.validar_rentabilidad(resultado)
            assert validacion['valido'] is True, f"Falló para campo: {campo}"


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE PORCENTAJES
# ══════════════════════════════════════════════════════════════

class TestPorcentajes:
    """Tests de validación de porcentajes"""
    
    def test_porcentajes_suman_100(self):
        """Porcentajes que suman exactamente 100% deben ser válidos"""
        # Arrange
        resultado = [
            {'area': 'Jurídica', 'porcentaje': 30},
            {'area': 'Notarial', 'porcentaje': 25},
            {'area': 'Contable', 'porcentaje': 45}
        ]
        
        # Act
        validacion = ValidadorSQL.validar_porcentaje(resultado)
        
        # Assert
        assert validacion['valido'] is True
    
    def test_porcentajes_suman_99(self):
        """Porcentajes que suman 99% (tolerancia) deben ser válidos"""
        # Arrange
        resultado = [
            {'area': 'A', 'porcentaje': 33},
            {'area': 'B', 'porcentaje': 33},
            {'area': 'C', 'porcentaje': 33}  # Suma 99
        ]
        
        # Act
        validacion = ValidadorSQL.validar_porcentaje(resultado)
        
        # Assert
        assert validacion['valido'] is True
    
    @pytest.mark.parametrize("porcentajes,debe_fallar", [
        ([30, 80], True),        # Suma 110%
        ([10, 20], True),        # Suma 30%
        ([50, 50, 50], True),    # Suma 150%
    ])
    def test_porcentajes_no_suman_100(self, porcentajes, debe_fallar):
        """Porcentajes que no suman ~100% deben fallar"""
        # Arrange
        resultado = [{'porcentaje': p} for p in porcentajes]
        
        # Act
        validacion = ValidadorSQL.validar_porcentaje(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'no suman 100%' in validacion['razon']
    
    def test_porcentaje_individual_fuera_rango(self):
        """Porcentaje individual >100% debe fallar"""
        # Arrange
        resultado = [{'porcentaje': 150}]
        
        # Act
        validacion = ValidadorSQL.validar_porcentaje(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'fuera de rango' in validacion['razon']


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE FACTURACIÓN
# ══════════════════════════════════════════════════════════════

class TestFacturacion:
    """Tests de validación de facturación"""
    
    @pytest.mark.parametrize("monto,es_dia", [
        (500_000, True),     # $500K día - normal
        (999_999, True),     # Casi 1M día - límite
        (100_000, True),     # $100K día - bajo pero válido
    ])
    def test_facturacion_dia_valida(self, monto, es_dia):
        """Facturación diaria dentro de límite"""
        # Arrange
        resultado = [{'total': monto}]
        
        # Act
        validacion = ValidadorSQL.validar_facturacion(resultado, es_dia=True)
        
        # Assert
        assert validacion['valido'] is True
    
    @pytest.mark.parametrize("monto", [
        5_000_000,      # $5M mes
        9_999_999,      # Casi 10M
        1_000_000,      # $1M mes
    ])
    def test_facturacion_mes_valida(self, monto):
        """Facturación mensual dentro de límite"""
        # Arrange
        resultado = [{'facturacion': monto}]
        
        # Act
        validacion = ValidadorSQL.validar_facturacion(resultado, es_dia=False)
        
        # Assert
        assert validacion['valido'] is True
    
    def test_facturacion_dia_excede_limite(self):
        """Facturación >$1M/día debe fallar"""
        # Arrange
        resultado = [{'ingresos': 1_500_000}]  # $1.5M en un día
        
        # Act
        validacion = ValidadorSQL.validar_facturacion(resultado, es_dia=True)
        
        # Assert
        assert validacion['valido'] is False
        assert 'fuera de rango' in validacion['razon']


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE GASTOS
# ══════════════════════════════════════════════════════════════

class TestGastos:
    """Tests de validación de gastos"""
    
    @pytest.mark.parametrize("monto,es_dia", [
        (100_000, True),     # $100K día
        (499_999, True),     # Casi límite día
        (2_000_000, False),  # $2M mes
        (4_999_999, False),  # Casi límite mes
    ])
    def test_gastos_validos(self, monto, es_dia):
        """Gastos dentro de límites razonables"""
        # Arrange
        resultado = [{'gastos': monto}]
        
        # Act
        validacion = ValidadorSQL.validar_gastos(resultado, es_dia=es_dia)
        
        # Assert
        assert validacion['valido'] is True
    
    def test_gastos_dia_excede_limite(self):
        """Gastos >$500K/día son sospechosos"""
        # Arrange
        resultado = [{'total_gastos': 600_000}]
        
        # Act
        validacion = ValidadorSQL.validar_gastos(resultado, es_dia=True)
        
        # Assert
        assert validacion['valido'] is False


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE RETIROS
# ══════════════════════════════════════════════════════════════

class TestRetiros:
    """Tests de validación de retiros de socios"""
    
    @pytest.mark.parametrize("monto", [
        50_000,      # $50K
        150_000,     # $150K
        199_999,     # Casi límite
    ])
    def test_retiros_validos(self, monto):
        """Retiros <$200K deben ser válidos"""
        # Arrange
        resultado = [{'retiros': monto}]
        
        # Act
        validacion = ValidadorSQL.validar_retiros(resultado)
        
        # Assert
        assert validacion['valido'] is True
    
    def test_retiro_negativo_invalido(self):
        """Retiros negativos son inválidos"""
        # Arrange
        resultado = [{'total_retiros': -10_000}]
        
        # Act
        validacion = ValidadorSQL.validar_retiros(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'negativo' in validacion['razon']


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE TIPO DE CAMBIO
# ══════════════════════════════════════════════════════════════

class TestTipoCambio:
    """Tests de validación de tipo de cambio UYU/USD"""
    
    @pytest.mark.parametrize("tc", [
        30.0,    # Límite inferior
        39.5,    # Normal
        42.3,    # Normal alto
        50.0,    # Límite superior
    ])
    def test_tipo_cambio_valido(self, tc):
        """Tipo de cambio 30-50 debe ser válido"""
        # Arrange
        resultado = [{'tipo_cambio_promedio': tc}]
        
        # Act
        validacion = ValidadorSQL.validar_tipo_cambio(resultado)
        
        # Assert
        assert validacion['valido'] is True
    
    @pytest.mark.parametrize("tc,debe_fallar", [
        (29.9, True),    # Bajo límite
        (51.0, True),    # Sobre límite
        (10.0, True),    # Muy bajo
        (100.0, True),   # Muy alto
    ])
    def test_tipo_cambio_invalido(self, tc, debe_fallar):
        """Tipo de cambio fuera de 30-50 debe fallar"""
        # Arrange
        resultado = [{'tipo_cambio': tc}]
        
        # Act
        validacion = ValidadorSQL.validar_tipo_cambio(resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'fuera de rango' in validacion['razon']


# ══════════════════════════════════════════════════════════════
# GRUPO 8: TESTS DE DETECTAR TIPO DE QUERY
# ══════════════════════════════════════════════════════════════

class TestDeteccionTipoQuery:
    """Tests de detección automática de tipo de query"""
    
    @pytest.mark.parametrize("pregunta,sql,tipo_esperado", [
        ("¿Cuánto recibió Bruno?", "SELECT SUM...", "distribucion_socio"),
        ("¿Cuánto retiró Agustina?", "SELECT...", "retiros"),
        ("¿Cuál es la rentabilidad?", "SELECT...", "rentabilidad"),
        ("¿Qué % facturamos en USD?", "SELECT * 100...", "porcentaje"),
        ("¿Cuánto facturamos hoy?", "SELECT...", "facturacion_dia"),
        ("¿Cuánto facturamos?", "SELECT...", "facturacion"),
        ("¿Cuánto gastamos hoy?", "SELECT...", "gastos_dia"),
        ("¿Cuánto gastamos?", "SELECT...", "gastos"),
        ("¿Cuál es el tipo de cambio?", "SELECT...", "tipo_cambio"),
    ])
    def test_detectar_tipo_query(self, pregunta, sql, tipo_esperado):
        """Debe detectar correctamente el tipo de query"""
        # Act
        tipo_detectado = ValidadorSQL.detectar_tipo_query(pregunta, sql)
        
        # Assert
        assert tipo_detectado == tipo_esperado


# ══════════════════════════════════════════════════════════════
# GRUPO 9: TESTS DE VALIDAR_RESULTADO (Método principal)
# ══════════════════════════════════════════════════════════════

class TestValidarResultado:
    """Tests del método principal validar_resultado"""
    
    def test_validar_resultado_distribucion_valida(self):
        """Distribución válida debe pasar todas las validaciones"""
        # Arrange
        pregunta = "¿Cuánto recibió Bruno este año?"
        sql = "SELECT SUM(monto_uyu) FROM..."
        resultado = [{'total': 45_000}]
        
        # Act
        validacion = ValidadorSQL.validar_resultado(pregunta, sql, resultado)
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['tipo_query'] == 'distribucion_socio'
        assert 'distribucion_socio' in validacion['validaciones_aplicadas']
    
    def test_validar_resultado_rentabilidad_invalida(self):
        """Rentabilidad >100% debe fallar"""
        # Arrange
        pregunta = "¿Cuál es la rentabilidad?"
        sql = "SELECT rentabilidad FROM..."
        resultado = [{'rentabilidad': 150}]
        
        # Act
        validacion = ValidadorSQL.validar_resultado(pregunta, sql, resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert validacion['tipo_query'] == 'rentabilidad'
        assert 'Rentabilidad' in validacion['razon']
    
    def test_validar_resultado_vacio(self):
        """Resultado vacío debe ser válido"""
        # Arrange
        pregunta = "Cualquier pregunta"
        sql = "SELECT..."
        resultado = []
        
        # Act
        validacion = ValidadorSQL.validar_resultado(pregunta, sql, resultado)
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['tipo_query'] == 'vacio'


# ══════════════════════════════════════════════════════════════
# GRUPO 10: TESTS DE VALIDACIÓN PRE-SQL
# ══════════════════════════════════════════════════════════════

class TestValidacionPreSQL:
    """Tests de validación ANTES de ejecutar SQL"""
    
    def test_ranking_con_limit_1_sospechoso(self):
        """Ranking pidiendo múltiples con LIMIT 1 debe detectarse"""
        # Arrange
        pregunta = "¿Cuáles son las mejores áreas?"
        sql = "SELECT area FROM operaciones ORDER BY ing DESC LIMIT 1"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        assert validacion['valido'] is False
        assert 'LIMIT 1' in validacion['problemas'][0]
    
    def test_ranking_limit_1_valido_con_cual(self):
        """'Cuál es el mejor' con LIMIT 1 debe ser válido"""
        # Arrange
        pregunta = "¿Cuál es el área más rentable?"
        sql = "SELECT area FROM operaciones ORDER BY rent DESC LIMIT 1"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        # Puede tener otros problemas pero no el de LIMIT 1
        problemas_limit = [p for p in validacion['problemas'] if 'LIMIT 1' in p]
        assert len(problemas_limit) == 0
    
    def test_proyeccion_sin_extract_month(self):
        """Proyección sin EXTRACT(MONTH) debe detectarse"""
        # Arrange
        pregunta = "¿Cuál es la proyección de fin de año?"
        sql = "SELECT ingresos * 1.5 as proyeccion FROM datos"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        assert validacion['valido'] is False
        assert any('Proyección sin calcular' in p for p in validacion['problemas'])
    
    def test_proyeccion_con_extract_month_valida(self):
        """Proyección con EXTRACT(MONTH FROM CURRENT_DATE) debe ser válida"""
        # Arrange
        pregunta = "Proyección fin de año"
        sql = "SELECT SUM(x) / EXTRACT(MONTH FROM CURRENT_DATE) * 12 FROM operaciones"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        # No debe tener el problema de proyección
        problemas_proyeccion = [p for p in validacion['problemas'] if 'Proyección' in p]
        assert len(problemas_proyeccion) == 0
    
    def test_porcentaje_moneda_sin_moneda_original(self):
        """Porcentaje de moneda sin usar moneda_original debe detectarse"""
        # Arrange
        pregunta = "¿Qué porcentaje de facturación es en USD?"
        sql = "SELECT SUM(monto_usd) * 100 / SUM(monto_uyu) FROM operaciones"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        assert validacion['valido'] is False
        assert any('moneda_original' in p for p in validacion['problemas'])
    
    def test_pregunta_generica_sin_filtro_temporal(self):
        """Pregunta sin período temporal debe detectarse"""
        # Arrange
        pregunta = "¿Cuánto facturamos?"
        sql = "SELECT SUM(monto) FROM operaciones WHERE deleted_at IS NULL"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        assert validacion['valido'] is False
        assert any('filtro temporal' in p for p in validacion['problemas'])
    
    def test_pregunta_con_periodo_explicito(self):
        """Pregunta con período explícito no debe requerir filtro adicional"""
        # Arrange
        pregunta = "¿Cuánto facturamos este mes?"
        sql = "SELECT SUM(monto) FROM operaciones WHERE DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)"
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        # No debe tener problema de filtro temporal
        problemas_temporal = [p for p in validacion['problemas'] if 'filtro temporal' in p]
        assert len(problemas_temporal) == 0


# ══════════════════════════════════════════════════════════════
# GRUPO 11: TESTS DE VALIDAR_RANGO (Método auxiliar)
# ══════════════════════════════════════════════════════════════

class TestValidarRango:
    """Tests del método validar_rango"""
    
    def test_valor_dentro_rango(self):
        """Valor dentro del rango debe ser válido"""
        # Act
        validacion = ValidadorSQL.validar_rango(50, 0, 100, "Test")
        
        # Assert
        assert validacion['valido'] is True
        assert validacion['razon'] is None
    
    def test_valor_en_limite_inferior(self):
        """Valor en límite inferior debe ser válido"""
        # Act
        validacion = ValidadorSQL.validar_rango(0, 0, 100, "Test")
        
        # Assert
        assert validacion['valido'] is True
    
    def test_valor_en_limite_superior(self):
        """Valor en límite superior debe ser válido"""
        # Act
        validacion = ValidadorSQL.validar_rango(100, 0, 100, "Test")
        
        # Assert
        assert validacion['valido'] is True
    
    def test_valor_fuera_rango_superior(self):
        """Valor sobre límite debe fallar"""
        # Act
        validacion = ValidadorSQL.validar_rango(101, 0, 100, "Porcentaje")
        
        # Assert
        assert validacion['valido'] is False
        assert 'fuera de rango' in validacion['razon']
        assert 'Porcentaje' in validacion['razon']
    
    def test_valor_none(self):
        """None debe considerarse válido (sin dato)"""
        # Act
        validacion = ValidadorSQL.validar_rango(None, 0, 100, "Test")
        
        # Assert
        assert validacion['valido'] is True


# ══════════════════════════════════════════════════════════════
# GRUPO 12: TESTS DE FUNCIÓN WRAPPER
# ══════════════════════════════════════════════════════════════

def test_validar_resultado_sql_wrapper():
    """Función wrapper debe llamar a ValidadorSQL.validar_resultado"""
    # Arrange
    pregunta = "¿Cuánto recibió Bruno?"
    sql = "SELECT SUM(monto) FROM distribuciones"
    resultado = [{'total': 30_000}]
    
    # Act
    validacion = validar_resultado_sql(pregunta, sql, resultado)
    
    # Assert
    assert 'valido' in validacion
    assert 'tipo_query' in validacion
    assert validacion['valido'] is True


# ══════════════════════════════════════════════════════════════
# GRUPO 13: TESTS DE CASOS EDGE
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos límite y edge cases"""
    
    def test_resultado_con_valores_none(self):
        """Resultado con valores None no debe crashear"""
        # Arrange
        pregunta = "¿Rentabilidad?"
        sql = "SELECT..."
        resultado = [{'rentabilidad': None}]
        
        # Act
        validacion = ValidadorSQL.validar_resultado(pregunta, sql, resultado)
        
        # Assert
        assert validacion['valido'] is True  # None se ignora
    
    def test_resultado_multiple_filas(self):
        """Debe validar resultado con múltiples filas"""
        # Arrange
        pregunta = "¿Distribuciones por socio?"
        sql = "SELECT..."
        resultado = [
            {'socio': 'Bruno', 'monto_uyu': 40_000},
            {'socio': 'Agustina', 'monto_uyu': 50_000},
            {'socio': 'Viviana', 'monto_uyu': 45_000},
        ]
        
        # Act
        validacion = ValidadorSQL.validar_resultado(pregunta, sql, resultado)
        
        # Assert
        assert validacion['valido'] is True
    
    def test_resultado_multiple_filas_una_invalida(self):
        """Si una fila es inválida, todo el resultado debe fallar"""
        # Arrange
        pregunta = "¿Distribuciones por socio?"
        sql = "SELECT..."
        resultado = [
            {'socio': 'Bruno', 'monto_uyu': 40_000},
            {'socio': 'Agustina', 'monto_uyu': -5_000},  # Negativo - inválido
        ]
        
        # Act
        validacion = ValidadorSQL.validar_resultado(pregunta, sql, resultado)
        
        # Assert
        assert validacion['valido'] is False
        assert 'negativo' in validacion['razon']
    
    def test_sql_vacio_en_validacion_pre(self):
        """SQL vacío no debe crashear validación pre-SQL"""
        # Arrange
        pregunta = "Test"
        sql = ""
        
        # Act
        validacion = ValidadorSQL.validar_sql_antes_ejecutar(pregunta, sql)
        
        # Assert
        # Debe retornar dict válido (aunque marque problemas)
        assert 'valido' in validacion
        assert 'problemas' in validacion
        assert isinstance(validacion['problemas'], list)


# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PYTEST
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def validador():
    """Fixture que retorna instancia de ValidadorSQL"""
    return ValidadorSQL()

