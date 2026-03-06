"""
Tests para informe_orquestador.py — Orquestador Multi-Query de Informes.

Ejecutar:
    cd backend
    pytest tests/test_informe_orquestador.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

from app.services.informe_orquestador import (
    es_pregunta_informe,
    extraer_periodo_informe,
    ejecutar_informe,
    ejecutar_informe_comparativo,
    computar_resumen_informe,
    _query_totales_por_tipo,
    _query_operativo_por_area,
    _query_distribuciones_por_socio,
    _query_retiros_por_localidad,
    _query_desglose_por_localidad,
    _query_evolucion_mensual,
    _query_composicion_por_moneda,
    _query_top_clientes,
    _query_top_proveedores,
    _ensamblar_totales,
    _calcular_variaciones,
    _serializar_valor,
)


# ══════════════════════════════════════════════════════════════
# GRUPO 1: DETECTOR DE INTENCIÓN INFORME
# ══════════════════════════════════════════════════════════════

class TestEsPreguntaInforme:
    """Tests para es_pregunta_informe()."""

    @pytest.mark.parametrize("pregunta", [
        "Dame un informe financiero completo del 2025",
        "informe completo 2024",
        "Quiero un resumen financiero del año 2025",
        "Cómo cerró el año 2024",
        "como cerro el año 2024",
        "situación financiera del 2025",
        "Necesito el reporte completo del 2025",
        "informe ejecutivo 2025",
        "resumen completo del 2025",
        "reporte financiero 2025",
        "dame el resumen ejecutivo del 2024",
        "informe general del 2025",
        "INFORME FINANCIERO COMPLETO DEL 2025",
    ])
    def test_detecta_informe(self, pregunta):
        assert es_pregunta_informe(pregunta) is True

    @pytest.mark.parametrize("pregunta", [
        "cuánto facturó el área jurídica",
        "gastos de enero 2025",
        "cuánto facturamos en 2025",
        "total de retiros",
        "rentabilidad por área en 2025",
        "ingresos por mes en 2024",
        "top 10 clientes de 2025",
        "ranking de proveedores",
        "comparar ingresos 2024 vs 2025",
        "cuál es la rentabilidad del año",
        "gastos por localidad",
        "distribuciones por socio en 2025",
    ])
    def test_no_detecta_pregunta_puntual(self, pregunta):
        assert es_pregunta_informe(pregunta) is False

    def test_string_vacio(self):
        assert es_pregunta_informe("") is False

    def test_pregunta_sin_keywords(self):
        assert es_pregunta_informe("hola qué tal") is False


# ══════════════════════════════════════════════════════════════
# GRUPO 2: EXTRACTOR DE PERÍODO
# ══════════════════════════════════════════════════════════════

class TestExtraerPeriodoInforme:
    """Tests para extraer_periodo_informe()."""

    def test_anio_completo(self):
        result = extraer_periodo_informe("informe del 2025")
        assert result is not None
        assert result["anio"] == 2025
        assert result["fecha_desde"] == "2025-01-01"
        assert result["fecha_hasta"] == "2025-12-31"
        assert result["tipo"] == "periodo"

    def test_anio_2024(self):
        result = extraer_periodo_informe("informe completo 2024")
        assert result["anio"] == 2024
        assert result["fecha_desde"] == "2024-01-01"
        assert result["fecha_hasta"] == "2024-12-31"

    def test_primer_semestre(self):
        result = extraer_periodo_informe("informe del primer semestre 2024")
        assert result["anio"] == 2024
        assert result["fecha_desde"] == "2024-01-01"
        assert result["fecha_hasta"] == "2024-06-30"

    def test_segundo_semestre(self):
        result = extraer_periodo_informe("resumen del segundo semestre 2025")
        assert result["fecha_desde"] == "2025-07-01"
        assert result["fecha_hasta"] == "2025-12-31"

    def test_primer_trimestre(self):
        result = extraer_periodo_informe("informe primer trimestre 2025")
        assert result["fecha_desde"] == "2025-01-01"
        assert result["fecha_hasta"] == "2025-03-31"

    def test_cuarto_trimestre(self):
        result = extraer_periodo_informe("informe cuarto trimestre 2024")
        assert result["fecha_desde"] == "2024-10-01"
        assert result["fecha_hasta"] == "2024-12-31"

    def test_comparativo_dos_anios(self):
        result = extraer_periodo_informe("informe comparativo 2024 vs 2025")
        assert result is not None
        assert result["tipo"] == "comparativo"
        assert len(result["periodos"]) == 2
        assert result["periodos"][0]["anio"] == 2024
        assert result["periodos"][1]["anio"] == 2025

    def test_sin_anio_retorna_none(self):
        result = extraer_periodo_informe("informe financiero")
        assert result is None

    def test_este_anio(self):
        from datetime import date
        result = extraer_periodo_informe("informe de este año")
        assert result is not None
        assert result["anio"] == date.today().year

    def test_del_ano_sin_tilde(self):
        from datetime import date
        result = extraer_periodo_informe("resumen del año")
        assert result is not None
        assert result["anio"] == date.today().year


# ══════════════════════════════════════════════════════════════
# GRUPO 3: QUERIES PREDEFINIDAS
# ══════════════════════════════════════════════════════════════

class TestQueriesPredefinidas:
    """Tests para las queries predefinidas del orquestador."""

    def _assert_query_segura(self, sql: str):
        """Verifica que la query es SELECT seguro."""
        import re
        sql_upper = sql.upper().strip()
        assert sql_upper.startswith("SELECT"), f"Query no empieza con SELECT: {sql[:50]}"
        # Buscar comandos peligrosos como statements (no como parte de "deleted_at")
        for cmd in ("DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"):
            pattern = rf'(^|;\s*){cmd}\b'
            assert not re.search(pattern, sql_upper), f"Query contiene statement {cmd}"
        assert ":fecha_desde" in sql, "Falta parametro :fecha_desde"
        assert ":fecha_hasta" in sql, "Falta parametro :fecha_hasta"
        assert "deleted_at IS NULL" in sql, "Falta filtro deleted_at IS NULL"

    def test_query_totales_por_tipo(self):
        sql = _query_totales_por_tipo()
        self._assert_query_segura(sql)
        assert "tipo_operacion" in sql
        assert "total_pesificado" in sql
        assert "total_dolarizado" in sql
        assert "GROUP BY" in sql.upper()

    def test_query_operativo_por_area(self):
        sql = _query_operativo_por_area()
        self._assert_query_segura(sql)
        assert "INNER JOIN areas" in sql
        assert "INGRESO" in sql
        assert "GASTO" in sql
        assert "rentabilidad" in sql.lower()

    def test_query_distribuciones_por_socio(self):
        sql = _query_distribuciones_por_socio()
        self._assert_query_segura(sql)
        assert "distribuciones_detalle" in sql
        assert "socios" in sql
        assert "dd.total_pesificado" in sql
        # NUNCA debe sumar o.total_pesificado (causa multiplicación x5)
        assert "o.total_pesificado" not in sql.split("SUM")[0] if "SUM" in sql else True

    def test_query_retiros_por_localidad(self):
        sql = _query_retiros_por_localidad()
        self._assert_query_segura(sql)
        assert "RETIRO" in sql
        assert "localidad" in sql
        assert "moneda_original" in sql

    def test_query_desglose_por_localidad(self):
        sql = _query_desglose_por_localidad()
        self._assert_query_segura(sql)
        assert "GROUP BY localidad" in sql
        assert "INGRESO" in sql
        assert "GASTO" in sql
        assert "RETIRO" in sql
        assert "DISTRIBUCION" in sql

    def test_query_evolucion_mensual(self):
        sql = _query_evolucion_mensual()
        self._assert_query_segura(sql)
        assert "EXTRACT(MONTH FROM fecha)" in sql
        assert "GROUP BY EXTRACT(MONTH FROM fecha)" in sql
        assert "total_operaciones" in sql

    def test_query_composicion_por_moneda(self):
        sql = _query_composicion_por_moneda()
        self._assert_query_segura(sql)
        assert "tipo_operacion" in sql
        assert "moneda_original" in sql
        assert "GROUP BY tipo_operacion, moneda_original" in sql

    def test_query_top_clientes(self):
        sql = _query_top_clientes()
        self._assert_query_segura(sql)
        assert "tipo_operacion = 'INGRESO'" in sql
        assert "cliente IS NOT NULL" in sql
        assert "cliente != ''" in sql
        assert "LIMIT 10" in sql

    def test_query_top_proveedores(self):
        sql = _query_top_proveedores()
        self._assert_query_segura(sql)
        assert "tipo_operacion = 'GASTO'" in sql
        assert "proveedor IS NOT NULL" in sql
        assert "proveedor != ''" in sql
        assert "LIMIT 10" in sql

    def test_ninguna_query_usa_union_all(self):
        queries = [
            _query_totales_por_tipo(),
            _query_operativo_por_area(),
            _query_distribuciones_por_socio(),
            _query_retiros_por_localidad(),
            _query_desglose_por_localidad(),
            _query_evolucion_mensual(),
            _query_composicion_por_moneda(),
            _query_top_clientes(),
            _query_top_proveedores(),
        ]
        for sql in queries:
            assert "UNION ALL" not in sql.upper(), f"Query usa UNION ALL: {sql[:100]}"

    def test_ninguna_query_usa_fstring(self):
        """Las queries deben usar :params, no f-strings."""
        queries = [
            _query_totales_por_tipo(),
            _query_operativo_por_area(),
            _query_distribuciones_por_socio(),
            _query_retiros_por_localidad(),
            _query_desglose_por_localidad(),
            _query_evolucion_mensual(),
            _query_composicion_por_moneda(),
            _query_top_clientes(),
            _query_top_proveedores(),
        ]
        for sql in queries:
            # No debe haber {variable} (señal de f-string)
            import re
            fstring_matches = re.findall(r'\{[a-z_]+\}', sql)
            assert len(fstring_matches) == 0, f"Query parece usar f-string: {fstring_matches}"


# ══════════════════════════════════════════════════════════════
# GRUPO 4: ENSAMBLADOR DE TOTALES
# ══════════════════════════════════════════════════════════════

class TestEnsamblarTotales:
    """Tests para _ensamblar_totales()."""

    def test_4_tipos(self):
        filas = [
            {"tipo_operacion": "INGRESO", "total_uyu": Decimal("34500000"), "total_usd": Decimal("850000"), "cantidad": 200},
            {"tipo_operacion": "GASTO", "total_uyu": Decimal("23100000"), "total_usd": Decimal("570000"), "cantidad": 150},
            {"tipo_operacion": "RETIRO", "total_uyu": Decimal("7443006"), "total_usd": Decimal("183000"), "cantidad": 88},
            {"tipo_operacion": "DISTRIBUCION", "total_uyu": Decimal("22975209"), "total_usd": Decimal("565000"), "cantidad": 75},
        ]
        totales = _ensamblar_totales(filas)

        assert totales["ingresos"]["uyu"] == 34500000.0
        assert totales["gastos"]["uyu"] == 23100000.0
        assert totales["retiros"]["uyu"] == 7443006.0
        assert totales["retiros"]["cantidad"] == 88
        assert totales["distribuciones"]["uyu"] == 22975209.0
        assert totales["distribuciones"]["cantidad"] == 75

        # Resultado neto = ingresos - gastos (NO retiros ni distribuciones)
        assert totales["resultado_neto"]["uyu"] == 11400000.0
        assert totales["resultado_neto"]["rentabilidad"] == 33.0

        # Capital de trabajo = ingresos - gastos - distribuciones
        esperado_capital = 34500000 - 23100000 - 22975209
        assert totales["capital_de_trabajo"]["uyu"] == esperado_capital

    def test_sin_retiros_ni_distribuciones(self):
        filas = [
            {"tipo_operacion": "INGRESO", "total_uyu": Decimal("10000"), "total_usd": Decimal("250"), "cantidad": 5},
            {"tipo_operacion": "GASTO", "total_uyu": Decimal("3000"), "total_usd": Decimal("75"), "cantidad": 3},
        ]
        totales = _ensamblar_totales(filas)
        assert totales["resultado_neto"]["uyu"] == 7000.0
        # Sin retiros/distribuciones → capital = resultado neto
        assert totales["capital_de_trabajo"]["uyu"] == 7000.0

    def test_lista_vacia(self):
        totales = _ensamblar_totales([])
        assert totales["resultado_neto"]["uyu"] == 0
        assert totales["resultado_neto"]["rentabilidad"] == 0

    def test_solo_gastos(self):
        filas = [
            {"tipo_operacion": "GASTO", "total_uyu": Decimal("5000"), "total_usd": Decimal("125"), "cantidad": 2},
        ]
        totales = _ensamblar_totales(filas)
        assert totales["resultado_neto"]["uyu"] == -5000.0
        assert totales["resultado_neto"]["rentabilidad"] == 0  # division por cero evitada


# ══════════════════════════════════════════════════════════════
# GRUPO 4.5: RESUMEN ENRIQUECIDO DE INFORME
# ══════════════════════════════════════════════════════════════

class TestComputarResumenInforme:
    """Tests para computar_resumen_informe()."""

    def test_computar_resumen_informe_estructura(self):
        resultado = {
            "totales": {
                "ingresos": {"uyu": 1000000, "usd": 25000, "cantidad": 50},
                "gastos": {"uyu": 500000, "usd": 12500, "cantidad": 30},
                "resultado_neto": {"uyu": 500000, "rentabilidad": 50.0},
                "retiros": {"uyu": 100000, "cantidad": 2},
                "distribuciones": {"uyu": 100000, "cantidad": 2},
                "capital_de_trabajo": {"uyu": 300000},
            },
            "concentracion_clientes": [
                {"ranking": 1, "cliente": "A", "participacion_pct": 20.0, "participacion_acumulada_pct": 20.0},
                {"ranking": 2, "cliente": "B", "participacion_pct": 15.0, "participacion_acumulada_pct": 35.0},
                {"ranking": 3, "cliente": "C", "participacion_pct": 10.0, "participacion_acumulada_pct": 45.0},
            ],
            "top_clientes": [
                {"cliente": "A", "total_uyu": 200000, "cantidad_operaciones": 5},
                {"cliente": "B", "total_uyu": 150000, "cantidad_operaciones": 3},
            ],
            "top_proveedores": [
                {"proveedor": "X", "total_uyu": 90000, "cantidad_operaciones": 2},
            ],
            "por_area": [
                {"area": "Jurídica", "ingresos_uyu": 600000, "gastos_uyu": 200000, "rentabilidad": 66.7},
            ],
            "por_localidad": [
                {"localidad": "MONTEVIDEO", "ingresos_uyu": 700000, "gastos_uyu": 300000, "rentabilidad": 57.1},
            ],
            "distribuciones_por_socio": [
                {"socio": "Bruno", "total_pesificado": 50000},
            ],
            "capital_trabajo": {
                "capital_trabajo_uyu": 300000,
                "ratio_distribuciones_sobre_ingresos": 10.0,
                "ratio_distribuciones_sobre_resultado": 20.0,
            },
        }

        resumen = computar_resumen_informe(resultado)
        assert "sumas" in resumen
        assert resumen["sumas"]["ingresos_uyu"] == 1000000
        assert "concentracion" in resumen
        assert resumen["concentracion"]["top_3_pct"] == 45.0
        assert "top_clientes" in resumen
        assert len(resumen["top_clientes"]) == 2
        assert "top_proveedores" in resumen
        assert "por_area" in resumen
        assert "por_localidad" in resumen
        assert "distribuciones_por_socio" in resumen
        assert "ratios_sostenibilidad" in resumen


# ══════════════════════════════════════════════════════════════
# GRUPO 5: CALCULAR VARIACIONES
# ══════════════════════════════════════════════════════════════

class TestCalcularVariaciones:
    """Tests para _calcular_variaciones()."""

    def test_variaciones_basicas(self):
        ant = {
            "ingresos": {"uyu": 100000},
            "gastos": {"uyu": 60000},
            "retiros": {"uyu": 10000},
            "distribuciones": {"uyu": 20000},
        }
        act = {
            "ingresos": {"uyu": 120000},
            "gastos": {"uyu": 70000},
            "retiros": {"uyu": 15000},
            "distribuciones": {"uyu": 25000},
        }
        var = _calcular_variaciones(ant, act)
        assert var["ingresos_uyu"]["absoluta"] == 20000
        assert var["ingresos_uyu"]["porcentual"] == 20.0
        assert var["gastos_uyu"]["absoluta"] == 10000
        assert var["retiros_uyu"]["absoluta"] == 5000
        assert var["distribuciones_uyu"]["absoluta"] == 5000

    def test_variacion_con_cero_anterior(self):
        ant = {"ingresos": {"uyu": 0}, "gastos": {"uyu": 0}, "retiros": {"uyu": 0}, "distribuciones": {"uyu": 0}}
        act = {"ingresos": {"uyu": 50000}, "gastos": {"uyu": 30000}, "retiros": {"uyu": 0}, "distribuciones": {"uyu": 0}}
        var = _calcular_variaciones(ant, act)
        assert var["ingresos_uyu"]["porcentual"] == 0  # division por cero evitada

    def test_variacion_negativa(self):
        ant = {"ingresos": {"uyu": 100000}, "gastos": {"uyu": 60000}, "retiros": {"uyu": 10000}, "distribuciones": {"uyu": 20000}}
        act = {"ingresos": {"uyu": 80000}, "gastos": {"uyu": 50000}, "retiros": {"uyu": 8000}, "distribuciones": {"uyu": 15000}}
        var = _calcular_variaciones(ant, act)
        assert var["ingresos_uyu"]["absoluta"] == -20000
        assert var["ingresos_uyu"]["porcentual"] == -20.0


# ══════════════════════════════════════════════════════════════
# GRUPO 6: SERIALIZACIÓN
# ══════════════════════════════════════════════════════════════

class TestSerializacion:
    """Tests para _serializar_valor."""

    def test_decimal(self):
        assert _serializar_valor(Decimal("1234.56")) == 1234.56

    def test_int(self):
        assert _serializar_valor(42) == 42

    def test_string(self):
        assert _serializar_valor("hola") == "hola"

    def test_none(self):
        assert _serializar_valor(None) is None


# ══════════════════════════════════════════════════════════════
# GRUPO 7: EJECUTOR PRINCIPAL (con mock de BD)
# ══════════════════════════════════════════════════════════════

class TestEjecutarInforme:
    """Tests para ejecutar_informe() con BD mockeada."""

    def _mock_db_con_datos(self):
        """Crea un mock de Session que retorna datos realistas."""
        db = MagicMock(spec=["execute"])

        # Simular 9 ejecuciones (1 por query)
        # Query 1: totales por tipo
        filas_tipo = self._make_rows([
            {"tipo_operacion": "INGRESO", "total_uyu": Decimal("34500000"), "total_usd": Decimal("850000"), "cantidad": 200},
            {"tipo_operacion": "GASTO", "total_uyu": Decimal("23100000"), "total_usd": Decimal("570000"), "cantidad": 150},
            {"tipo_operacion": "RETIRO", "total_uyu": Decimal("7443006"), "total_usd": Decimal("183000"), "cantidad": 88},
            {"tipo_operacion": "DISTRIBUCION", "total_uyu": Decimal("22975209"), "total_usd": Decimal("565000"), "cantidad": 75},
        ])
        # Query 2: por area
        filas_area = self._make_rows([
            {"area": "Jurídica", "ingresos_uyu": Decimal("15000000"), "ingresos_usd": Decimal("370000"),
             "gastos_uyu": Decimal("8000000"), "gastos_usd": Decimal("197000"),
             "neto_uyu": Decimal("7000000"), "rentabilidad": Decimal("46.7")},
        ])
        # Query 3: distribuciones por socio
        filas_dist = self._make_rows([
            {"socio": "Bruno", "monto_uyu": Decimal("4595042"), "monto_usd": Decimal("113000"),
             "porcentaje": Decimal("20.00"), "cantidad_distribuciones": 75},
        ])
        # Query 4: retiros por localidad
        filas_ret = self._make_rows([
            {"localidad": "MONTEVIDEO", "moneda_original": "UYU",
             "total_uyu": Decimal("5000000"), "total_usd": Decimal("123000"), "cantidad": 50},
        ])
        # Query 5: desglose por localidad
        filas_loc = self._make_rows([
            {
                "localidad": "MONTEVIDEO",
                "ingresos_uyu": Decimal("24000000"),
                "ingresos_usd": Decimal("592000"),
                "gastos_uyu": Decimal("16000000"),
                "gastos_usd": Decimal("394000"),
                "retiros_uyu": Decimal("5000000"),
                "retiros_usd": Decimal("123000"),
                "distribuciones_uyu": Decimal("15000000"),
                "distribuciones_usd": Decimal("370000"),
            },
            {
                "localidad": "MERCEDES",
                "ingresos_uyu": Decimal("10500000"),
                "ingresos_usd": Decimal("258000"),
                "gastos_uyu": Decimal("7100000"),
                "gastos_usd": Decimal("176000"),
                "retiros_uyu": Decimal("2443006"),
                "retiros_usd": Decimal("60000"),
                "distribuciones_uyu": Decimal("7975209"),
                "distribuciones_usd": Decimal("195000"),
            },
        ])
        # Query 6: evolución mensual
        filas_mes = self._make_rows([
            {"mes": 1, "ingresos_uyu": Decimal("3000000"), "gastos_uyu": Decimal("1800000"), "retiros_uyu": Decimal("500000"), "distribuciones_uyu": Decimal("1200000"), "total_operaciones": 40},
            {"mes": 2, "ingresos_uyu": Decimal("3200000"), "gastos_uyu": Decimal("1900000"), "retiros_uyu": Decimal("600000"), "distribuciones_uyu": Decimal("1300000"), "total_operaciones": 42},
        ])
        # Query 7: composición por moneda
        filas_moneda = self._make_rows([
            {"tipo_operacion": "INGRESO", "moneda_original": "UYU", "total_uyu": Decimal("25000000"), "cantidad": 150},
            {"tipo_operacion": "INGRESO", "moneda_original": "USD", "total_uyu": Decimal("9500000"), "cantidad": 50},
        ])
        # Query 8: top clientes
        filas_clientes = self._make_rows([
            {"cliente": "Cliente A", "total_uyu": Decimal("1200000"), "total_usd": Decimal("29600"), "cantidad_operaciones": 12},
        ])
        # Query 9: top proveedores
        filas_proveedores = self._make_rows([
            {"proveedor": "Proveedor X", "total_uyu": Decimal("900000"), "total_usd": Decimal("22200"), "cantidad_operaciones": 10},
        ])

        db.execute.side_effect = [
            filas_tipo, filas_area, filas_dist, filas_ret,
            filas_loc, filas_mes, filas_moneda, filas_clientes, filas_proveedores,
        ]
        return db

    def _make_rows(self, dicts: list) -> MagicMock:
        """Crea un mock de Result que itera sobre filas."""
        rows = []
        for d in dicts:
            row = MagicMock()
            row._mapping = d
            rows.append(row)
        result = MagicMock()
        result.__iter__ = MagicMock(return_value=iter(rows))
        return result

    def test_informe_completo_estructura(self):
        db = self._mock_db_con_datos()
        result = ejecutar_informe(db, "informe financiero completo del 2025")

        assert result is not None
        assert result["tipo"] == "informe_completo"
        assert result["periodo"]["anio"] == 2025
        assert "totales" in result
        assert "por_area" in result
        assert "distribuciones_por_socio" in result
        assert "retiros_por_localidad" in result
        assert "por_localidad" in result
        assert "evolucion_mensual" in result
        assert "composicion_por_moneda" in result
        assert "top_clientes" in result
        assert "top_proveedores" in result

    def test_informe_nuevas_secciones_no_none(self):
        db = self._mock_db_con_datos()
        result = ejecutar_informe(db, "informe financiero completo del 2025")

        assert result["por_localidad"] is not None
        assert result["evolucion_mensual"] is not None
        assert result["composicion_por_moneda"] is not None
        assert result["top_clientes"] is not None
        assert result["top_proveedores"] is not None

    def test_informe_incluye_retiros(self):
        db = self._mock_db_con_datos()
        result = ejecutar_informe(db, "informe completo 2025")

        assert result["totales"]["retiros"]["uyu"] == 7443006.0
        assert result["totales"]["retiros"]["cantidad"] == 88

    def test_informe_incluye_distribuciones(self):
        db = self._mock_db_con_datos()
        result = ejecutar_informe(db, "informe completo 2025")

        assert result["totales"]["distribuciones"]["uyu"] == 22975209.0
        assert len(result["distribuciones_por_socio"]) > 0

    def test_informe_calcula_resultado_neto(self):
        db = self._mock_db_con_datos()
        result = ejecutar_informe(db, "informe completo 2025")

        neto = result["totales"]["resultado_neto"]
        assert neto["uyu"] == 34500000.0 - 23100000.0
        assert neto["rentabilidad"] > 0

    def test_informe_calcula_capital_trabajo(self):
        db = self._mock_db_con_datos()
        result = ejecutar_informe(db, "informe completo 2025")

        capital = result["totales"]["capital_de_trabajo"]["uyu"]
        esperado = 34500000.0 - 23100000.0 - 22975209.0
        assert capital == esperado

    def test_informe_sin_anio_retorna_none(self):
        db = MagicMock()
        result = ejecutar_informe(db, "informe financiero")
        assert result is None

    def test_informe_error_bd_retorna_none(self):
        db = MagicMock()
        db.execute.side_effect = Exception("Connection refused")
        result = ejecutar_informe(db, "informe completo 2025")
        assert result is None


# ══════════════════════════════════════════════════════════════
# GRUPO 8: EJECUTOR COMPARATIVO (con mock de BD)
# ══════════════════════════════════════════════════════════════

class TestEjecutarInformeComparativo:
    """Tests para ejecutar_informe_comparativo() con BD mockeada."""

    def _mock_db_comparativo(self):
        """Mock que retorna datos para 2 periodos (18 queries)."""
        db = MagicMock(spec=["execute"])

        def make_rows(dicts):
            rows = []
            for d in dicts:
                row = MagicMock()
                row._mapping = d
                rows.append(row)
            result = MagicMock()
            result.__iter__ = MagicMock(return_value=iter(rows))
            return result

        # 2 periodos x 9 queries = 18 ejecuciones
        tipo_2024 = make_rows([
            {"tipo_operacion": "INGRESO", "total_uyu": Decimal("30000000"), "total_usd": Decimal("740000"), "cantidad": 180},
            {"tipo_operacion": "GASTO", "total_uyu": Decimal("20000000"), "total_usd": Decimal("494000"), "cantidad": 130},
            {"tipo_operacion": "RETIRO", "total_uyu": Decimal("5000000"), "total_usd": Decimal("123000"), "cantidad": 60},
            {"tipo_operacion": "DISTRIBUCION", "total_uyu": Decimal("15000000"), "total_usd": Decimal("370000"), "cantidad": 50},
        ])
        area_2024 = make_rows([{"area": "Jurídica", "ingresos_uyu": Decimal("12000000"), "ingresos_usd": Decimal("296000"), "gastos_uyu": Decimal("6000000"), "gastos_usd": Decimal("148000"), "neto_uyu": Decimal("6000000"), "rentabilidad": Decimal("50.0")}])
        dist_2024 = make_rows([{"socio": "Bruno", "monto_uyu": Decimal("3000000"), "monto_usd": Decimal("74000"), "porcentaje": Decimal("20.00"), "cantidad_distribuciones": 50}])
        ret_2024 = make_rows([{"localidad": "MONTEVIDEO", "moneda_original": "UYU", "total_uyu": Decimal("3000000"), "total_usd": Decimal("74000"), "cantidad": 40}])
        loc_2024 = make_rows([{"localidad": "MONTEVIDEO", "ingresos_uyu": Decimal("20000000"), "ingresos_usd": Decimal("493000"), "gastos_uyu": Decimal("12000000"), "gastos_usd": Decimal("296000"), "retiros_uyu": Decimal("3000000"), "retiros_usd": Decimal("74000"), "distribuciones_uyu": Decimal("9000000"), "distribuciones_usd": Decimal("222000")}])
        mes_2024 = make_rows([{"mes": 1, "ingresos_uyu": Decimal("2500000"), "gastos_uyu": Decimal("1500000"), "retiros_uyu": Decimal("300000"), "distribuciones_uyu": Decimal("700000"), "total_operaciones": 35}])
        moneda_2024 = make_rows([{"tipo_operacion": "INGRESO", "moneda_original": "UYU", "total_uyu": Decimal("21000000"), "cantidad": 130}])
        cli_2024 = make_rows([{"cliente": "Cliente A", "total_uyu": Decimal("900000"), "total_usd": Decimal("22200"), "cantidad_operaciones": 9}])
        prov_2024 = make_rows([{"proveedor": "Proveedor X", "total_uyu": Decimal("700000"), "total_usd": Decimal("17200"), "cantidad_operaciones": 8}])

        tipo_2025 = make_rows([
            {"tipo_operacion": "INGRESO", "total_uyu": Decimal("34500000"), "total_usd": Decimal("850000"), "cantidad": 200},
            {"tipo_operacion": "GASTO", "total_uyu": Decimal("23100000"), "total_usd": Decimal("570000"), "cantidad": 150},
            {"tipo_operacion": "RETIRO", "total_uyu": Decimal("7443006"), "total_usd": Decimal("183000"), "cantidad": 88},
            {"tipo_operacion": "DISTRIBUCION", "total_uyu": Decimal("22975209"), "total_usd": Decimal("565000"), "cantidad": 75},
        ])
        area_2025 = make_rows([{"area": "Jurídica", "ingresos_uyu": Decimal("15000000"), "ingresos_usd": Decimal("370000"), "gastos_uyu": Decimal("8000000"), "gastos_usd": Decimal("197000"), "neto_uyu": Decimal("7000000"), "rentabilidad": Decimal("46.7")}])
        dist_2025 = make_rows([{"socio": "Bruno", "monto_uyu": Decimal("4595042"), "monto_usd": Decimal("113000"), "porcentaje": Decimal("20.00"), "cantidad_distribuciones": 75}])
        ret_2025 = make_rows([{"localidad": "MONTEVIDEO", "moneda_original": "UYU", "total_uyu": Decimal("5000000"), "total_usd": Decimal("123000"), "cantidad": 50}])
        loc_2025 = make_rows([{"localidad": "MONTEVIDEO", "ingresos_uyu": Decimal("24000000"), "ingresos_usd": Decimal("592000"), "gastos_uyu": Decimal("16000000"), "gastos_usd": Decimal("394000"), "retiros_uyu": Decimal("5000000"), "retiros_usd": Decimal("123000"), "distribuciones_uyu": Decimal("15000000"), "distribuciones_usd": Decimal("370000")}])
        mes_2025 = make_rows([{"mes": 1, "ingresos_uyu": Decimal("3000000"), "gastos_uyu": Decimal("1800000"), "retiros_uyu": Decimal("500000"), "distribuciones_uyu": Decimal("1200000"), "total_operaciones": 40}])
        moneda_2025 = make_rows([{"tipo_operacion": "INGRESO", "moneda_original": "UYU", "total_uyu": Decimal("25000000"), "cantidad": 150}])
        cli_2025 = make_rows([{"cliente": "Cliente A", "total_uyu": Decimal("1200000"), "total_usd": Decimal("29600"), "cantidad_operaciones": 12}])
        prov_2025 = make_rows([{"proveedor": "Proveedor X", "total_uyu": Decimal("900000"), "total_usd": Decimal("22200"), "cantidad_operaciones": 10}])

        db.execute.side_effect = [
            tipo_2024, area_2024, dist_2024, ret_2024, loc_2024, mes_2024, moneda_2024, cli_2024, prov_2024,
            tipo_2025, area_2025, dist_2025, ret_2025, loc_2025, mes_2025, moneda_2025, cli_2025, prov_2025,
        ]
        return db

    def test_comparativo_estructura(self):
        db = self._mock_db_comparativo()
        result = ejecutar_informe_comparativo(db, "informe comparativo 2024 vs 2025")

        assert result is not None
        assert result["tipo"] == "informe_comparativo"
        assert len(result["periodos"]) == 2
        assert "variaciones" in result

    def test_comparativo_variaciones(self):
        db = self._mock_db_comparativo()
        result = ejecutar_informe_comparativo(db, "informe comparativo 2024 vs 2025")

        var = result["variaciones"]
        # Ingresos: 34.5M - 30M = 4.5M
        assert var["ingresos_uyu"]["absoluta"] == 4500000.0
        assert var["ingresos_uyu"]["porcentual"] == 15.0

    def test_comparativo_sin_anios_retorna_none(self):
        db = MagicMock()
        result = ejecutar_informe_comparativo(db, "informe comparativo")
        assert result is None

    def test_comparativo_cada_periodo_tiene_secciones(self):
        db = self._mock_db_comparativo()
        result = ejecutar_informe_comparativo(db, "informe 2024 vs 2025")

        for p in result["periodos"]:
            assert "totales" in p
            assert "por_area" in p
            assert "distribuciones_por_socio" in p
            assert "retiros_por_localidad" in p
            assert "por_localidad" in p
            assert "evolucion_mensual" in p
            assert "composicion_por_moneda" in p
            assert "top_clientes" in p
            assert "top_proveedores" in p
