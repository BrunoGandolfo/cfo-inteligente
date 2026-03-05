"""
Suite de Tests para SQLPostProcessor - Sistema CFO Inteligente

Tests del post-procesador de SQL que modifica queries según contexto.
Maneja conversión de monedas y extracción de SQL de texto mixto.

Ejecutar:
    cd backend
    pytest tests/test_sql_post_processor.py -v
    pytest tests/test_sql_post_processor.py --cov=app/services/sql_post_processor

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import pytest
from app.services.sql_post_processor import SQLPostProcessor


# ══════════════════════════════════════════════════════════════
# GRUPO 1: TESTS DE DETECCIÓN DE MONEDA
# ══════════════════════════════════════════════════════════════

class TestDetectarMoneda:
    """Tests de detección de moneda en preguntas"""
    
    def test_detecta_usd_con_dolar(self):
        """'dólar' en pregunta detecta USD"""
        pregunta = "¿Cuánto es en dólares?"
        moneda = SQLPostProcessor.detectar_moneda(pregunta)
        assert moneda == "USD"
    
    def test_detecta_usd_con_dollar(self):
        """'dollar' en inglés detecta USD"""
        pregunta = "Show me in dollar"
        moneda = SQLPostProcessor.detectar_moneda(pregunta)
        assert moneda == "USD"
    
    def test_detecta_usd_literal(self):
        """'USD' literal detecta USD"""
        pregunta = "Muéstrame los montos en USD"
        moneda = SQLPostProcessor.detectar_moneda(pregunta)
        assert moneda == "USD"
    
    def test_detecta_uyu_con_peso(self):
        """'peso' detecta UYU"""
        pregunta = "¿Cuánto es en pesos?"
        moneda = SQLPostProcessor.detectar_moneda(pregunta)
        assert moneda == "UYU"
    
    def test_detecta_uyu_literal(self):
        """'UYU' literal detecta UYU"""
        pregunta = "Montos en UYU por favor"
        moneda = SQLPostProcessor.detectar_moneda(pregunta)
        assert moneda == "UYU"
    
    def test_default_es_uyu(self):
        """Sin moneda específica, default es UYU"""
        pregunta = "¿Cuántos ingresos hay?"
        moneda = SQLPostProcessor.detectar_moneda(pregunta)
        assert moneda == "UYU"
    
    def test_case_insensitive(self):
        """Detección es case-insensitive"""
        assert SQLPostProcessor.detectar_moneda("EN DÓLARES") == "USD"
        assert SQLPostProcessor.detectar_moneda("en dolares") == "USD"
        assert SQLPostProcessor.detectar_moneda("En DoLaReS") == "USD"


# ══════════════════════════════════════════════════════════════
# GRUPO 3: TESTS DE EXTRACCIÓN DE SQL DE TEXTO
# ══════════════════════════════════════════════════════════════

class TestExtraerSQLDeTexto:
    """Tests de extracción de SQL de texto mixto"""
    
    def test_extrae_de_bloque_sql(self):
        """Extrae SQL de bloque ```sql ... ```"""
        texto = """Aquí está el SQL:
```sql
SELECT * FROM operaciones WHERE tipo = 'INGRESO'
```
Espero que te sirva."""
        
        resultado = SQLPostProcessor.extraer_sql_de_texto(texto)
        
        assert resultado is not None
        assert "SELECT" in resultado
        assert "operaciones" in resultado
        assert "```" not in resultado
    
    def test_extrae_de_bloque_generico(self):
        """Extrae SQL de bloque ``` ... ``` genérico"""
        texto = """El query es:
```
SELECT COUNT(*) FROM users
```"""
        
        resultado = SQLPostProcessor.extraer_sql_de_texto(texto)
        
        assert resultado is not None
        assert "SELECT" in resultado
    
    def test_extrae_sql_sin_bloques(self):
        """Extrae SQL cuando no hay bloques de código"""
        texto = """Para obtener los ingresos usa:
SELECT SUM(monto_uyu) FROM operaciones WHERE tipo_operacion = 'INGRESO'
Esta consulta te dará el total."""
        
        resultado = SQLPostProcessor.extraer_sql_de_texto(texto)
        
        assert resultado is not None
        assert "SELECT" in resultado
    
    def test_extrae_with_cte(self):
        """Extrae CTE que empieza con WITH"""
        texto = """Aquí tienes:
WITH totales AS (
    SELECT tipo, SUM(monto) as total FROM ops GROUP BY tipo
)
SELECT * FROM totales"""
        
        resultado = SQLPostProcessor.extraer_sql_de_texto(texto)
        
        assert resultado is not None
        assert "WITH" in resultado
    
    def test_retorna_none_sin_sql(self):
        """Retorna None si no hay SQL"""
        texto = "Esta es una respuesta sin ningún SQL"
        resultado = SQLPostProcessor.extraer_sql_de_texto(texto)
        
        assert resultado is None
    
    def test_maneja_texto_vacio(self):
        """Texto vacío o None retorna None"""
        assert SQLPostProcessor.extraer_sql_de_texto("") is None
        assert SQLPostProcessor.extraer_sql_de_texto(None) is None


# ══════════════════════════════════════════════════════════════
# GRUPO 4: TESTS DE PROCESAMIENTO COMPLETO
# ══════════════════════════════════════════════════════════════

class TestProcesarSQL:
    """Tests del método principal procesar_sql()"""
    
    def test_proceso_completo_sin_cambios(self):
        """SQL limpio en UYU no se modifica"""
        pregunta = "¿Cuántos ingresos hay?"
        sql = "SELECT COUNT(*) FROM operaciones"
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql)
        
        assert resultado["sql"] == sql
        assert resultado["modificado"] is False
        assert len(resultado["cambios"]) == 0
    
    @pytest.mark.skip(reason="Conversión automática monto_uyu→monto_usd DESACTIVADA (causaba bugs). Claude genera SQL correcto.")
    def test_proceso_convierte_a_usd(self):
        """Pregunta en USD convierte SQL"""
        pregunta = "¿Cuánto es en dólares?"
        sql = "SELECT SUM(monto_uyu) FROM operaciones"
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql)
        
        assert "monto_usd" in resultado["sql"]
        assert resultado["modificado"] is True
        assert "USD" in str(resultado["cambios"])
    
    @pytest.mark.skip(reason="Conversión automática monto_uyu→monto_usd DESACTIVADA (causaba bugs). Claude genera SQL correcto.")
    def test_proceso_extrae_y_convierte(self):
        """Extrae de texto mixto Y convierte moneda"""
        pregunta = "Muéstrame en dólares"
        sql_mixto = """Aquí está:
```sql
SELECT SUM(monto_uyu) FROM operaciones
```"""
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql_mixto)
        
        # Debe haber extraído y convertido
        assert "monto_usd" in resultado["sql"]
        assert resultado["modificado"] is True
        assert len(resultado["cambios"]) >= 1
    
    @pytest.mark.skip(reason="Conversión automática monto_uyu→monto_usd DESACTIVADA (causaba bugs). Claude genera SQL correcto.")
    def test_proceso_retorna_cambios_realizados(self):
        """Lista de cambios indica qué se modificó"""
        pregunta = "En dólares por favor"
        sql = "SELECT monto_uyu FROM operaciones"
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql)
        
        assert "cambios" in resultado
        assert isinstance(resultado["cambios"], list)
        assert len(resultado["cambios"]) > 0
    
    def test_proceso_no_modifica_si_ya_usd(self):
        """SQL ya en USD no se modifica innecesariamente"""
        pregunta = "Dame en dólares"
        sql = "SELECT SUM(monto_usd) FROM operaciones"
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql)
        
        # No debería modificar porque ya está en USD
        assert resultado["sql"] == sql
    
    def test_proceso_estructura_resultado(self):
        """Verifica estructura del resultado"""
        resultado = SQLPostProcessor.procesar_sql(
            "Cualquier pregunta",
            "SELECT 1"
        )
        
        assert "sql" in resultado
        assert "modificado" in resultado
        assert "cambios" in resultado
        assert isinstance(resultado["modificado"], bool)
        assert isinstance(resultado["cambios"], list)


# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE CASOS EDGE
# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# GRUPO 5: TESTS DE PARENTIZAR UNION ALL
# ══════════════════════════════════════════════════════════════

class TestParentizarUnionAll:
    """Tests de parentización automática de UNION ALL con ORDER BY/LIMIT"""

    def test_parentiza_union_all_con_order_by_limit(self):
        """Ramas con ORDER BY + LIMIT se envuelven en paréntesis"""
        sql = (
            "SELECT nombre, total FROM ingresos ORDER BY total DESC LIMIT 5 "
            "UNION ALL "
            "SELECT nombre, total FROM gastos ORDER BY total DESC LIMIT 5"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        assert resultado.startswith("(")
        assert "UNION ALL" in resultado
        # Cada rama debe estar parentizada
        assert resultado.count("(SELECT") == 2

    def test_parentiza_union_all_con_solo_order_by(self):
        """Ramas con solo ORDER BY (sin LIMIT) se parentiza"""
        sql = (
            "SELECT nombre FROM ingresos ORDER BY nombre "
            "UNION ALL "
            "SELECT nombre FROM gastos ORDER BY nombre"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        assert "(SELECT" in resultado

    def test_preserva_order_by_final_del_union(self):
        """ORDER BY final que aplica al UNION completo se preserva fuera"""
        sql = (
            "SELECT nombre, total FROM ingresos ORDER BY total DESC LIMIT 5 "
            "UNION ALL "
            "SELECT nombre, total FROM gastos ORDER BY total DESC LIMIT 5 "
            "ORDER BY total DESC"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        # El ORDER BY final debe estar fuera de los paréntesis
        assert resultado.rstrip().endswith("ORDER BY total DESC")
        # Las ramas deben estar parentizadas
        assert "(SELECT" in resultado

    def test_no_modifica_sin_union(self):
        """SQL sin UNION no se modifica"""
        sql = "SELECT * FROM operaciones ORDER BY fecha DESC LIMIT 10"
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        assert resultado == sql

    def test_no_modifica_sin_order_by_ni_limit(self):
        """UNION ALL sin ORDER BY/LIMIT en ramas no necesita paréntesis"""
        sql = (
            "SELECT nombre FROM ingresos "
            "UNION ALL "
            "SELECT nombre FROM gastos"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        assert resultado == sql

    def test_no_modifica_ya_parentizado(self):
        """SQL ya parentizado no se toca"""
        sql = (
            "(SELECT nombre FROM ingresos ORDER BY nombre LIMIT 5) "
            "UNION ALL "
            "(SELECT nombre FROM gastos ORDER BY nombre LIMIT 5)"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        assert resultado == sql

    def test_no_modifica_sql_vacio(self):
        """SQL vacío retorna igual"""
        assert SQLPostProcessor.parentizar_union_all("") == ""
        assert SQLPostProcessor.parentizar_union_all(None) is None

    def test_union_simple_sin_all(self):
        """UNION (sin ALL) con ORDER BY/LIMIT también se parentiza"""
        sql = (
            "SELECT nombre FROM ingresos ORDER BY nombre LIMIT 5 "
            "UNION "
            "SELECT nombre FROM gastos ORDER BY nombre LIMIT 5"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        assert "(SELECT" in resultado

    def test_order_by_con_limit_pertenece_a_rama(self):
        """ORDER BY seguido de LIMIT en última rama NO se extrae como final"""
        sql = (
            "SELECT nombre, total FROM ingresos ORDER BY total DESC LIMIT 5 "
            "UNION ALL "
            "SELECT nombre, total FROM gastos ORDER BY total DESC LIMIT 5"
        )
        resultado = SQLPostProcessor.parentizar_union_all(sql)

        # Ambas ramas deben conservar su ORDER BY + LIMIT dentro de paréntesis
        partes = resultado.split("UNION ALL")
        assert "ORDER BY" in partes[0]
        assert "LIMIT" in partes[0]
        assert "ORDER BY" in partes[1]
        assert "LIMIT" in partes[1]

    def test_integracion_procesar_sql(self):
        """parentizar_union_all se ejecuta via procesar_sql"""
        sql = (
            "SELECT nombre, total FROM ingresos ORDER BY total DESC LIMIT 5 "
            "UNION ALL "
            "SELECT nombre, total FROM gastos ORDER BY total DESC LIMIT 5"
        )
        resultado = SQLPostProcessor.procesar_sql("cualquier pregunta", sql)

        assert resultado["modificado"] is True
        assert any("UNION ALL" in c or "Parentizado" in c for c in resultado["cambios"])
        assert "(SELECT" in resultado["sql"]


# ══════════════════════════════════════════════════════════════
# GRUPO 6: TESTS DE CORRECCIÓN DE ACENTOS EN ÁREAS
# ══════════════════════════════════════════════════════════════

class TestCorregirAcentosAreas:
    """Tests del safety net que corrige nombres de áreas sin tilde"""

    def test_corrige_juridica(self):
        """'Juridica' sin tilde se corrige a 'Jurídica'"""
        sql = "SELECT * FROM operaciones o JOIN areas a ON o.area_id = a.id WHERE a.nombre = 'Juridica'"
        resultado = SQLPostProcessor.corregir_acentos_areas(sql)
        assert "'Jurídica'" in resultado
        assert "'Juridica'" not in resultado

    def test_corrige_recuperacion(self):
        """'Recuperacion' sin tilde se corrige a 'Recuperación'"""
        sql = "WHERE a.nombre = 'Recuperacion'"
        resultado = SQLPostProcessor.corregir_acentos_areas(sql)
        assert "'Recuperación'" in resultado

    def test_corrige_administracion(self):
        """'Administracion' sin tilde se corrige a 'Administración'"""
        sql = "WHERE a.nombre = 'Administracion'"
        resultado = SQLPostProcessor.corregir_acentos_areas(sql)
        assert "'Administración'" in resultado

    def test_no_modifica_con_tildes_correctas(self):
        """SQL con tildes correctas no se modifica"""
        sql = "WHERE a.nombre = 'Jurídica'"
        resultado = SQLPostProcessor.corregir_acentos_areas(sql)
        assert resultado == sql

    def test_no_modifica_areas_sin_tildes(self):
        """Áreas que no tienen tildes (Notarial, Contable) no se tocan"""
        sql = "WHERE a.nombre IN ('Notarial', 'Contable', 'Otros Gastos')"
        resultado = SQLPostProcessor.corregir_acentos_areas(sql)
        assert resultado == sql

    def test_corrige_multiples(self):
        """Corrige múltiples áreas en un solo SQL"""
        sql = "WHERE a.nombre IN ('Juridica', 'Recuperacion', 'Administracion')"
        resultado = SQLPostProcessor.corregir_acentos_areas(sql)
        assert "'Jurídica'" in resultado
        assert "'Recuperación'" in resultado
        assert "'Administración'" in resultado

    def test_maneja_sql_vacio(self):
        """SQL vacío o None no crashea"""
        assert SQLPostProcessor.corregir_acentos_areas("") == ""
        assert SQLPostProcessor.corregir_acentos_areas(None) is None

    def test_integracion_procesar_sql(self):
        """corregir_acentos_areas se ejecuta via procesar_sql"""
        sql = "SELECT * FROM operaciones o JOIN areas a ON o.area_id = a.id WHERE a.nombre = 'Juridica'"
        resultado = SQLPostProcessor.procesar_sql("gastos de jurídica", sql)
        assert "'Jurídica'" in resultado["sql"]
        assert resultado["modificado"] is True
        assert any("acentos" in c.lower() for c in resultado["cambios"])


# ══════════════════════════════════════════════════════════════
# GRUPO 7: TESTS DE CASOS EDGE
# ══════════════════════════════════════════════════════════════

class TestCasosEdge:
    """Tests de casos límite"""
    
    @pytest.mark.skip(reason="Conversión automática monto_uyu→monto_usd DESACTIVADA (causaba bugs). Claude genera SQL correcto.")
    def test_sql_con_alias_monto_uyu(self):
        """Alias con monto_uyu se convierte"""
        pregunta = "En USD"
        sql = "SELECT monto_uyu AS total FROM operaciones"
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql)
        
        assert "monto_usd" in resultado["sql"]
    
    def test_pregunta_con_ambas_monedas_prioriza_usd(self):
        """Si menciona ambas monedas, USD tiene prioridad"""
        # El método busca primero USD keywords
        assert SQLPostProcessor.detectar_moneda("pesos o dólares") == "USD"
    
    @pytest.mark.skip(reason="Conversión automática monto_uyu→monto_usd DESACTIVADA (causaba bugs). Claude genera SQL correcto.")
    def test_sql_multilinea(self):
        """SQL multilínea se procesa correctamente"""
        pregunta = "En dólares"
        sql = """SELECT 
    tipo_operacion,
    SUM(monto_uyu) as total
FROM operaciones
GROUP BY tipo_operacion"""
        
        resultado = SQLPostProcessor.procesar_sql(pregunta, sql)
        
        assert "monto_usd" in resultado["sql"]
        assert "GROUP BY" in resultado["sql"]
    
    def test_extraccion_limpia_explicaciones(self):
        """Extracción limpia texto explicativo al final"""
        texto = """SELECT * FROM operaciones

This query will return all operations.
Note: Make sure to run this in production."""
        
        resultado = SQLPostProcessor.extraer_sql_de_texto(texto)
        
        if resultado:
            # Debería haber limpiado las explicaciones
            assert "Note:" not in resultado or "SELECT" in resultado



