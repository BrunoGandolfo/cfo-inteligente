"""
Tests para _computar_resumen — pre-cómputo de totales para el prompt narrativo.

Ejecutar:
    cd backend
    pytest tests/test_computar_resumen.py -v
"""

import pytest
from decimal import Decimal
from app.api.cfo_streaming import _computar_resumen


class TestComputarResumenBasico:
    """Tests básicos de _computar_resumen."""

    def test_datos_vacios_retorna_dict_vacio(self):
        assert _computar_resumen([]) == {}
        assert _computar_resumen(None) == {}

    def test_una_fila_sin_agrupacion(self):
        datos = [{"total_pesificado": 1000000}]
        res = _computar_resumen(datos)
        assert res["total_filas"] == 1
        assert res["sumas"]["total_pesificado"] == 1000000
        assert "maximo" not in res  # Solo 1 fila, no hay max/min

    def test_sumas_multiples_filas(self):
        datos = [
            {"area": "Jurídica", "total": 100},
            {"area": "Contable", "total": 200},
            {"area": "Notarial", "total": 300},
        ]
        res = _computar_resumen(datos)
        assert res["sumas"]["total"] == 600
        assert res["total_filas"] == 3


class TestComputarResumenMaxMin:
    """Tests de máximos y mínimos con referencia."""

    def test_max_min_con_agrupacion(self):
        datos = [
            {"area": "Jurídica", "total": 500},
            {"area": "Contable", "total": 100},
            {"area": "Notarial", "total": 800},
        ]
        res = _computar_resumen(datos)
        assert res["maximo"]["total"]["valor"] == 800
        assert res["maximo"]["total"]["fila"] == "Notarial"
        assert res["minimo"]["total"]["valor"] == 100
        assert res["minimo"]["total"]["fila"] == "Contable"

    def test_max_min_sin_columna_agrupacion_usa_string(self):
        datos = [
            {"descripcion": "Pago A", "monto": 50},
            {"descripcion": "Pago B", "monto": 150},
        ]
        res = _computar_resumen(datos)
        assert res["maximo"]["monto"]["valor"] == 150
        assert res["maximo"]["monto"]["fila"] == "Pago B"

    def test_una_fila_no_genera_max_min(self):
        datos = [{"area": "Jurídica", "total": 500}]
        res = _computar_resumen(datos)
        assert "maximo" not in res
        assert "minimo" not in res


class TestComputarResumenSubtotales:
    """Tests de subtotales por columna de agrupación."""

    def test_subtotales_por_area(self):
        datos = [
            {"area": "Jurídica", "monto": 100},
            {"area": "Jurídica", "monto": 200},
            {"area": "Contable", "monto": 50},
        ]
        res = _computar_resumen(datos)
        sub = res["subtotales_por_area"]
        assert sub["Jurídica"]["monto"] == 300
        assert sub["Contable"]["monto"] == 50

    def test_subtotales_por_localidad(self):
        datos = [
            {"localidad": "Montevideo", "ingreso": 1000},
            {"localidad": "Montevideo", "ingreso": 2000},
            {"localidad": "Mercedes", "ingreso": 500},
        ]
        res = _computar_resumen(datos)
        sub = res["subtotales_por_localidad"]
        assert sub["Montevideo"]["ingreso"] == 3000
        assert sub["Mercedes"]["ingreso"] == 500

    def test_sin_subtotales_si_un_solo_grupo(self):
        """Si todas las filas tienen el mismo valor de agrupación, no generar subtotales."""
        datos = [
            {"area": "Jurídica", "monto": 100},
            {"area": "Jurídica", "monto": 200},
        ]
        res = _computar_resumen(datos)
        assert "subtotales_por_area" not in res  # Solo 1 grupo → no útil

    def test_sin_subtotales_si_mas_de_20_grupos(self):
        """Más de 20 grupos distintos no genera subtotales (demasiado ruido)."""
        datos = [{"area": f"Area_{i}", "monto": i * 100} for i in range(25)]
        res = _computar_resumen(datos)
        assert "subtotales_por_area" not in res


class TestComputarResumenPorcentajes:
    """Tests de exclusión de columnas de porcentaje."""

    def test_no_suma_porcentajes(self):
        datos = [
            {"area": "Jurídica", "total": 100, "porcentaje": 40},
            {"area": "Contable", "total": 150, "rentabilidad": 33.5},
        ]
        res = _computar_resumen(datos)
        assert "porcentaje" not in res["sumas"]
        assert "rentabilidad" not in res["sumas"]
        assert "total" in res["sumas"]

    def test_no_suma_participacion(self):
        datos = [
            {"area": "A", "total": 100, "participacion": 50},
            {"area": "B", "total": 200, "participacion": 50},
        ]
        res = _computar_resumen(datos)
        assert "participacion" not in res["sumas"]


class TestComputarResumenDecimal:
    """Tests con valores Decimal (como los devuelve PostgreSQL)."""

    def test_sumas_con_decimal(self):
        datos = [
            {"area": "Jurídica", "total": Decimal("15234567.89")},
            {"area": "Contable", "total": Decimal("9876543.21")},
        ]
        res = _computar_resumen(datos)
        assert res["sumas"]["total"] == 25111111.10

    def test_max_min_con_decimal(self):
        datos = [
            {"area": "Jurídica", "total": Decimal("500")},
            {"area": "Contable", "total": Decimal("200")},
        ]
        res = _computar_resumen(datos)
        assert res["maximo"]["total"]["valor"] == 500
        assert res["minimo"]["total"]["valor"] == 200


class TestComputarResumenSinNumericos:
    """Tests con datos sin columnas numéricas."""

    def test_solo_strings_retorna_total_filas(self):
        datos = [
            {"area": "Jurídica", "localidad": "Montevideo"},
            {"area": "Contable", "localidad": "Mercedes"},
        ]
        res = _computar_resumen(datos)
        assert res["total_filas"] == 2
        assert "sumas" not in res

    def test_valores_none_ignorados(self):
        datos = [
            {"area": "Jurídica", "total": 100},
            {"area": "Contable", "total": None},
        ]
        res = _computar_resumen(datos)
        assert res["sumas"]["total"] == 100


class TestComputarResumenMultiplesColumnas:
    """Tests con múltiples columnas numéricas."""

    def test_sumas_multiples_columnas_numericas(self):
        datos = [
            {"area": "Jurídica", "ingresos": 1000, "gastos": 400},
            {"area": "Contable", "ingresos": 2000, "gastos": 600},
        ]
        res = _computar_resumen(datos)
        assert res["sumas"]["ingresos"] == 3000
        assert res["sumas"]["gastos"] == 1000

    def test_subtotales_multiples_columnas(self):
        datos = [
            {"area": "Jurídica", "ingresos": 1000, "gastos": 400},
            {"area": "Jurídica", "ingresos": 500, "gastos": 200},
            {"area": "Contable", "ingresos": 2000, "gastos": 600},
        ]
        res = _computar_resumen(datos)
        sub = res["subtotales_por_area"]
        assert sub["Jurídica"]["ingresos"] == 1500
        assert sub["Jurídica"]["gastos"] == 600
        assert sub["Contable"]["ingresos"] == 2000
