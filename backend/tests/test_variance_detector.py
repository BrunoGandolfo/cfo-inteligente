"""
Tests para VarianceDetector.
Datos normales y con varianza alta.
"""
import pytest
from app.services.analytics.variance_detector import VarianceDetector


class TestVarianceDetectorInit:
    """Tests del constructor."""

    def test_init_default_thresholds(self):
        d = VarianceDetector()
        assert d.threshold_percent == 10.0
        assert d.threshold_margin_pp == 5.0

    def test_init_custom_thresholds(self):
        d = VarianceDetector(threshold_percent=15.0, threshold_margin_pp=7.0)
        assert d.threshold_percent == 15.0
        assert d.threshold_margin_pp == 7.0


class TestVarianceDetectorDetectVariances:
    """detect_variances con datos normales y con varianza."""

    def test_detect_variances_sin_varianza_significativa_returns_empty(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": 3,
            "variacion_mom_gastos": -2,
            "variacion_mom_rentabilidad": 1,
            "ingresos_uyu": 103000,
            "gastos_uyu": 98000,
            "margen_neto": 31,
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 100000,
            "margen_neto": 30,
        }
        variances = detector.detect_variances(actual, anterior)
        assert len(variances) == 0

    def test_detect_variances_revenue_alta_varianza_favorable(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": 25,
            "ingresos_uyu": 125000,
            "gastos_uyu": 100000,
            "margen_neto": 35,
            "porcentaje_ingresos_por_area": {"Jurídica": 60, "Contable": 40},
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 100000,
            "margen_neto": 30,
            "porcentaje_ingresos_por_area": {"Jurídica": 50, "Contable": 50},
        }
        variances = detector.detect_variances(actual, anterior)
        revenue_v = [v for v in variances if v["tipo"] == "revenue"]
        assert len(revenue_v) >= 1
        assert revenue_v[0]["direccion"] == "favorable"
        assert revenue_v[0]["variacion_pct"] == 25

    def test_detect_variances_revenue_alta_varianza_desfavorable(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": -15,
            "ingresos_uyu": 85000,
            "gastos_uyu": 80000,
            "margen_neto": 28,
            "porcentaje_ingresos_por_area": {"Jurídica": 45, "Contable": 55},
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 80000,
            "margen_neto": 30,
            "porcentaje_ingresos_por_area": {"Jurídica": 50, "Contable": 50},
        }
        variances = detector.detect_variances(actual, anterior)
        revenue_v = [v for v in variances if v["tipo"] == "revenue"]
        assert len(revenue_v) >= 1
        assert revenue_v[0]["direccion"] == "desfavorable"

    def test_detect_variances_expense_alta_varianza(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": 0,
            "variacion_mom_gastos": 22,
            "ingresos_uyu": 100000,
            "gastos_uyu": 122000,
            "margen_neto": 25,
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 100000,
            "margen_neto": 30,
        }
        variances = detector.detect_variances(actual, anterior)
        expense_v = [v for v in variances if v["tipo"] == "expense"]
        assert len(expense_v) >= 1
        assert expense_v[0]["direccion"] == "desfavorable"

    def test_detect_variances_margin_alta_varianza(self):
        detector = VarianceDetector(threshold_margin_pp=5.0)
        actual = {
            "variacion_mom_ingresos": -5,
            "variacion_mom_gastos": 10,
            "variacion_mom_rentabilidad": -8,
            "ingresos_uyu": 95000,
            "gastos_uyu": 80000,
            "margen_neto": 22,
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 70000,
            "margen_neto": 30,
        }
        variances = detector.detect_variances(actual, anterior)
        margin_v = [v for v in variances if v["tipo"] == "margin"]
        assert len(margin_v) >= 1
        assert "Margen" in margin_v[0]["metrica"]


class TestVarianceDetectorSeveridad:
    """Severidad CRÍTICO vs ALTO según umbrales."""

    def test_detect_variances_revenue_critico_mas_20(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": -25,
            "ingresos_uyu": 75000,
            "gastos_uyu": 70000,
            "margen_neto": 28,
            "porcentaje_ingresos_por_area": {"Jurídica": 50, "Contable": 50},
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 70000,
            "margen_neto": 30,
            "porcentaje_ingresos_por_area": {"Jurídica": 50, "Contable": 50},
        }
        variances = detector.detect_variances(actual, anterior)
        revenue_v = [v for v in variances if v["tipo"] == "revenue"]
        assert len(revenue_v) >= 1
        assert revenue_v[0]["severidad"] == "CRÍTICO"

    def test_detect_variances_ordenado_por_severidad(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": -25,
            "variacion_mom_gastos": 15,
            "variacion_mom_rentabilidad": -12,
            "ingresos_uyu": 75000,
            "gastos_uyu": 115000,
            "margen_neto": 20,
            "porcentaje_ingresos_por_area": {"Jurídica": 50},
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 100000,
            "margen_neto": 32,
            "porcentaje_ingresos_por_area": {"Jurídica": 50},
        }
        variances = detector.detect_variances(actual, anterior)
        severidad_orden = {"CRÍTICO": 1, "ALTO": 2, "MEDIO": 3, "BAJO": 4}
        for i in range(len(variances) - 1):
            assert severidad_orden.get(variances[i]["severidad"], 5) <= severidad_orden.get(
                variances[i + 1]["severidad"], 5
            )


class TestVarianceDetectorExplicaciones:
    """Explicaciones y acciones requeridas."""

    def test_detect_variances_incluye_explicacion_y_accion(self):
        detector = VarianceDetector(threshold_percent=10.0)
        actual = {
            "variacion_mom_ingresos": 15,
            "ingresos_uyu": 115000,
            "gastos_uyu": 100000,
            "margen_neto": 32,
            "porcentaje_ingresos_por_area": {"Jurídica": 55, "Contable": 45},
        }
        anterior = {
            "ingresos_uyu": 100000,
            "gastos_uyu": 100000,
            "margen_neto": 30,
            "porcentaje_ingresos_por_area": {"Jurídica": 50, "Contable": 50},
        }
        variances = detector.detect_variances(actual, anterior)
        for v in variances:
            assert "explicacion" in v
            assert "accion" in v
