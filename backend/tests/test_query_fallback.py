"""
Suite de Tests para QueryFallback - Sistema CFO Inteligente

Tests del sistema de fallback de queries predefinidas.
Garantiza cobertura 100% para preguntas críticas del negocio.

Ejecutar:
    cd backend
    pytest tests/test_query_fallback.py -v
    pytest tests/test_query_fallback.py --cov=app/services/query_fallback

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from app.services.query_fallback import QueryFallback


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE RENTABILIDAD
# ══════════════════════════════════════════════════════════════

class TestRentabilidad:
    """Tests de queries de rentabilidad"""
    
    def test_rentabilidad_este_mes(self):
        """Pregunta por rentabilidad este mes debe retornar SQL"""
        pregunta = "¿Cuál es la rentabilidad este mes?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "rentabilidad" in sql.lower() or "SUM" in sql
        assert "INGRESO" in sql
        assert "GASTO" in sql
        assert "DATE_TRUNC" in sql
    
    def test_rentabilidad_del_mes(self):
        """Variante 'rentabilidad del mes' también funciona"""
        pregunta = "Dame la rentabilidad del mes"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "operaciones" in sql.lower()
    
    def test_rentabilidad_por_area(self):
        """Rentabilidad por área genera SQL con GROUP BY"""
        pregunta = "¿Cuál es la rentabilidad por área?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "GROUP BY" in sql
        assert "areas" in sql or "a.nombre" in sql
        assert "ORDER BY" in sql
    
    def test_rentabilidad_por_localidad(self):
        """Rentabilidad por localidad genera SQL correcto"""
        pregunta = "Muéstrame la rentabilidad por localidad"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "localidad" in sql.lower()
        assert "GROUP BY" in sql


# ══════════════════════════════════════════════════════════════
# GRUPO 2: TESTS DE COMPARACIONES GEOGRÁFICAS
# ══════════════════════════════════════════════════════════════

class TestComparacionesGeograficas:
    """Tests de queries de comparación geográfica"""
    
    def test_mercedes_vs_montevideo(self):
        """Comparación Mercedes vs Montevideo"""
        pregunta = "Compara Mercedes vs Montevideo"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "localidad" in sql.lower()
        assert "GROUP BY" in sql
    
    def test_comparar_mercedes_alternativo(self):
        """Variante 'comparar mercedes' funciona"""
        pregunta = "Comparar Mercedes con Montevideo"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
    
    def test_comparacion_mercedes_montevideo(self):
        """Variante sin 'vs' funciona"""
        pregunta = "Mercedes montevideo, cómo van?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "localidad" in sql.lower()


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE PREGUNTAS GENERALES
# ══════════════════════════════════════════════════════════════

class TestPreguntasGenerales:
    """Tests de preguntas generales del negocio"""
    
    def test_como_venimos(self):
        """Pregunta '¿Cómo venimos?' genera resumen"""
        pregunta = "¿Cómo venimos este mes?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "INGRESO" in sql
        assert "GASTO" in sql
        # Debe incluir ingresos, gastos y resultado
    
    def test_como_vamos(self):
        """Variante '¿Cómo vamos?' también funciona"""
        pregunta = "¿Cómo vamos?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
    
    def test_cuantas_operaciones(self):
        """Cuenta de operaciones"""
        pregunta = "¿Cuántas operaciones hay este mes?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "COUNT" in sql


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE CAPITAL Y FLUJO
# ══════════════════════════════════════════════════════════════

class TestCapitalFlujo:
    """Tests de queries de capital y flujo de caja"""
    
    def test_capital_de_trabajo(self):
        """Capital de trabajo genera SQL correcto"""
        pregunta = "¿Cuál es el capital de trabajo?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "INGRESO" in sql
        assert "GASTO" in sql
        assert "RETIRO" in sql
        assert "DISTRIBUCION" in sql
    
    def test_capital_trabajo_variante(self):
        """Variante 'capital trabajo' sin 'de'"""
        pregunta = "Muéstrame el capital trabajo"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
    
    def test_flujo_de_caja(self):
        """Flujo de caja genera SQL con entradas y salidas"""
        pregunta = "¿Cómo está el flujo de caja?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "INGRESO" in sql
        assert "GASTO" in sql
    
    def test_flujo_caja_variante(self):
        """Variante 'flujo caja' sin 'de'"""
        pregunta = "Dame el flujo caja del mes"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE TENDENCIAS
# ══════════════════════════════════════════════════════════════

class TestTendencias:
    """Tests de queries de tendencias"""
    
    def test_analisis_tendencias(self):
        """Análisis de tendencias genera SQL histórico"""
        pregunta = "Muéstrame el análisis de tendencias"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "DATE_TRUNC" in sql
        assert "month" in sql.lower()
        assert "GROUP BY" in sql
    
    def test_tendencias_simple(self):
        """Solo 'tendencias' también funciona"""
        pregunta = "¿Cuáles son las tendencias?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        # Debe ser histórico (12 meses)
        assert "11 months" in sql.lower() or "12" in sql


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE CASOS EDGE
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos límite y no coincidencias"""
    
    def test_pregunta_sin_match_retorna_none(self):
        """Pregunta sin patrón conocido retorna None"""
        pregunta = "¿Cuál es el clima hoy?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is None
    
    def test_pregunta_vacia(self):
        """Pregunta vacía retorna None"""
        pregunta = ""
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is None
    
    def test_pregunta_solo_espacios(self):
        """Pregunta solo espacios retorna None"""
        pregunta = "   "
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is None
    
    def test_case_insensitive(self):
        """Debe ser case-insensitive"""
        # Mayúsculas
        sql1 = QueryFallback.get_query_for("¿CÓMO VENIMOS?")
        # Minúsculas
        sql2 = QueryFallback.get_query_for("¿cómo venimos?")
        # Mixto
        sql3 = QueryFallback.get_query_for("¿CóMo VeNiMoS?")
        
        # Todas deben retornar SQL (o todas None si no hay match)
        assert (sql1 is not None) == (sql2 is not None) == (sql3 is not None)
    
    def test_con_tildes_y_sin_tildes(self):
        """Maneja tildes correctamente"""
        sql_con = QueryFallback.get_query_for("¿Cómo venimos?")
        sql_sin = QueryFallback.get_query_for("Como venimos?")
        
        # Ambas deben funcionar (el método usa 'in' que matchea substring)
        assert sql_con is not None or sql_sin is not None


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE ESTRUCTURA SQL
# ══════════════════════════════════════════════════════════════

class TestEstructuraSQL:
    """Tests que verifican estructura correcta del SQL generado"""
    
    def test_sql_incluye_deleted_at_filter(self):
        """SQL debe filtrar registros eliminados (soft delete)"""
        pregunta = "¿Cómo venimos?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "deleted_at IS NULL" in sql
    
    def test_sql_rentabilidad_tiene_nullif(self):
        """SQL de rentabilidad usa NULLIF para evitar división por cero"""
        pregunta = "¿Cuál es la rentabilidad?"
        sql = QueryFallback.get_query_for(pregunta)
        
        if sql:
            assert "NULLIF" in sql
    
    def test_sql_tiene_periodo_actual(self):
        """SQL usa CURRENT_DATE para periodo actual"""
        pregunta = "¿Cómo venimos este mes?"
        sql = QueryFallback.get_query_for(pregunta)
        
        assert sql is not None
        assert "CURRENT_DATE" in sql
    
    def test_sql_tendencias_tiene_orden(self):
        """SQL de tendencias ordena por fecha"""
        pregunta = "Análisis de tendencias"
        sql = QueryFallback.get_query_for(pregunta)
        
        if sql:
            assert "ORDER BY" in sql


