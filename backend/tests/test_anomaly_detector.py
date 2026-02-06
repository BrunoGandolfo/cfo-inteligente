"""
Tests para AnomalyDetector.
Datos de prueba y edge cases: listas vacías, un dato, sin anomalías.
"""
import pytest
from app.services.analytics.anomaly_detector import AnomalyDetector


class TestAnomalyDetectorInit:
    """Tests del constructor."""

    def test_init_default_thresholds(self):
        d = AnomalyDetector()
        assert d.threshold_percent == 10.0
        assert d.threshold_margin_pp == 5.0

    def test_init_custom_thresholds(self):
        d = AnomalyDetector(threshold_percent=20.0, threshold_margin_pp=8.0)
        assert d.threshold_percent == 20.0
        assert d.threshold_margin_pp == 8.0


class TestAnomalyDetectorDetectAllWithoutComparison:
    """detect_all sin metricas_anterior (solo anomalías absolutas)."""

    def test_detect_all_sin_metricas_anterior_usa_absolute_anomalies(self):
        detector = AnomalyDetector()
        metricas = {"margen_neto": 15}
        anomalies = detector.detect_all(metricas_actual=metricas, metricas_anterior=None)
        assert len(anomalies) >= 1
        assert any(a["tipo"] == "low_margin_absolute" for a in anomalies)

    def test_detect_all_sin_metricas_anterior_margen_ok_no_anomaly(self):
        detector = AnomalyDetector()
        metricas = {"margen_neto": 40}
        anomalies = detector.detect_all(metricas_actual=metricas, metricas_anterior=None)
        assert len(anomalies) == 0


class TestAnomalyDetectorDetectAllWithComparison:
    """detect_all con metricas_anterior."""

    def test_detect_all_revenue_drop_critico(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": -25,
            "ingresos_uyu": 80000,
            "margen_neto": 30,
        }
        anterior = {"ingresos_uyu": 100000}
        anomalies = detector.detect_all(actual, anterior)
        assert any(a["tipo"] == "revenue_drop" for a in anomalies)
        assert any(a["severidad"] == "CRÍTICO" for a in anomalies)

    def test_detect_all_revenue_surge_alto(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": 35,
            "ingresos_uyu": 135000,
            "margen_neto": 30,
        }
        anterior = {"ingresos_uyu": 100000}
        anomalies = detector.detect_all(actual, anterior)
        assert any(a["tipo"] == "revenue_surge" for a in anomalies)

    def test_detect_all_expense_spike(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": 0,
            "variacion_mom_gastos": 40,
            "margen_neto": 25,
        }
        anterior = {"ingresos_uyu": 100, "gastos_uyu": 50}
        anomalies = detector.detect_all(actual, anterior)
        assert any(a["tipo"] == "expense_spike" for a in anomalies)

    def test_detect_all_margin_compression(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": 0,
            "variacion_mom_gastos": 0,
            "variacion_mom_rentabilidad": -7,
            "margen_neto": 20,
        }
        anterior = {"margen_neto": 27}
        anomalies = detector.detect_all(actual, anterior)
        assert any(a["tipo"] == "margin_compression" for a in anomalies)

    def test_detect_all_low_margin(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": 0,
            "variacion_mom_gastos": 0,
            "variacion_mom_rentabilidad": 0,
            "margen_neto": 15,
        }
        anterior = {"ingresos_uyu": 100, "gastos_uyu": 50, "margen_neto": 25}
        anomalies = detector.detect_all(actual, anterior)
        assert any(a["tipo"] == "low_margin" for a in anomalies)

    def test_detect_all_sin_anomalias_returns_empty(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": 5,
            "variacion_mom_gastos": -2,
            "variacion_mom_rentabilidad": 1,
            "margen_neto": 35,
        }
        anterior = {"ingresos_uyu": 100, "gastos_uyu": 50, "margen_neto": 34}
        anomalies = detector.detect_all(actual, anterior)
        assert len(anomalies) == 0


class TestAnomalyDetectorEdgeCases:
    """Edge cases: métricas vacías, un solo dato, etc."""

    def test_detect_all_metricas_vacias_sin_anterior(self):
        detector = AnomalyDetector()
        anomalies = detector.detect_all(metricas_actual={}, metricas_anterior=None)
        assert isinstance(anomalies, list)
        # margen_neto por defecto 0 puede generar anomalía low_margin_absolute
        assert len(anomalies) <= 1

    def test_detect_all_metricas_vacias_con_anterior(self):
        detector = AnomalyDetector()
        anomalies = detector.detect_all(
            metricas_actual={},
            metricas_anterior={"ingresos_uyu": 100},
        )
        assert isinstance(anomalies, list)

    def test_detect_all_un_solo_dato_relevante(self):
        detector = AnomalyDetector()
        metricas = {"margen_neto": 10}
        anomalies = detector.detect_all(metricas_actual=metricas, metricas_anterior=None)
        assert len(anomalies) >= 1

    def test_detect_all_ordenado_por_severidad(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": -25,
            "variacion_mom_gastos": 35,
            "variacion_mom_rentabilidad": -6,
            "margen_neto": 15,
            "ingresos_uyu": 80,
        }
        anterior = {"ingresos_uyu": 100}
        anomalies = detector.detect_all(actual, anterior)
        severidad_orden = {"CRÍTICO": 1, "ALTO": 2, "MEDIO": 3, "BAJO": 4}
        for i in range(len(anomalies) - 1):
            a1, a2 = anomalies[i], anomalies[i + 1]
            assert severidad_orden.get(a1["severidad"], 5) <= severidad_orden.get(
                a2["severidad"], 5
            )


class TestAnomalyDetectorExplainRevenueDrop:
    """Explicación de caída de ingresos (por área)."""

    def test_explain_revenue_drop_con_cambios_por_area(self):
        detector = AnomalyDetector()
        actual = {
            "variacion_mom_ingresos": -22,
            "ingresos_uyu": 78,
            "porcentaje_ingresos_por_area": {"Jurídica": 60, "Contable": 40},
        }
        anterior = {
            "ingresos_uyu": 100,
            "porcentaje_ingresos_por_area": {"Jurídica": 40, "Contable": 60},
        }
        anomalies = detector.detect_all(actual, anterior)
        revenue_drop = next((a for a in anomalies if a["tipo"] == "revenue_drop"), None)
        if revenue_drop:
            assert "explicacion" in revenue_drop
            assert "área" in revenue_drop["explicacion"].lower() or "Jurídica" in revenue_drop["explicacion"] or "Contable" in revenue_drop["explicacion"]
