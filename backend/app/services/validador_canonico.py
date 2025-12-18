"""
Validador Canónico - Compara respuestas del CFO AI contra queries de control

Sistema de validación automática que:
- Identifica si una pregunta coincide con queries canónicas conocidas
- Ejecuta queries de control pre-validadas
- Compara resultados y genera advertencias si difieren >1%

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional
import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class ValidadorCanonico:
    """
    Sistema de validación que compara respuestas del CFO AI 
    contra queries de control pre-definidas.
    
    Objetivo: Garantizar 99%+ de precisión en cifras financieras críticas.
    """
    
    # ══════════════════════════════════════════════════════════════
    # QUERIES CANÓNICAS DE VALIDACIÓN
    # ══════════════════════════════════════════════════════════════
    
    QUERIES_CANONICAS = {
        # === FACTURACIÓN ===
        "facturacion_2025": {
            "patrones": ["facturación 2025", "facturamos 2025", "ingresos 2025", 
                        "facturación este año", "facturamos este año", "ingresos este año"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2025
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01  # 1%
        },
        "facturacion_2024": {
            "patrones": ["facturación 2024", "facturamos 2024", "ingresos 2024"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2024
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        "facturacion_mes_actual": {
            "patrones": ["facturación este mes", "facturamos este mes", "ingresos del mes"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
                AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === GASTOS ===
        "gastos_2025": {
            "patrones": ["gastos 2025", "gastamos 2025", "gastos este año"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2025
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        "gastos_2024": {
            "patrones": ["gastos 2024", "gastamos 2024"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2024
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === RENTABILIDAD ===
        "rentabilidad_2025": {
            "patrones": ["rentabilidad 2025", "rentabilidad este año", "margen 2025"],
            "sql_control": """
                SELECT ROUND(
                    (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END) -
                     SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END)) /
                    NULLIF(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END), 0) * 100
                , 2) as porcentaje FROM operaciones 
                WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
            """,
            "campo_resultado": "porcentaje",
            "tolerancia": 0.5  # 0.5 puntos porcentuales
        },
        "rentabilidad_mes_actual": {
            "patrones": ["rentabilidad este mes", "rentabilidad del mes", "margen del mes"],
            "sql_control": """
                SELECT ROUND(
                    (SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END) -
                     SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END)) /
                    NULLIF(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END), 0) * 100
                , 2) as porcentaje FROM operaciones 
                WHERE deleted_at IS NULL 
                AND DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)
            """,
            "campo_resultado": "porcentaje",
            "tolerancia": 0.5
        },
        
        # === CAPITAL Y FLUJO ===
        "capital_trabajo": {
            "patrones": ["capital de trabajo", "capital trabajo", "capital disponible"],
            "sql_control": """
                SELECT SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END) -
                       SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END) -
                       SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN monto_uyu ELSE 0 END) -
                       SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN monto_uyu ELSE 0 END) as total
                FROM operaciones WHERE deleted_at IS NULL
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === POR LOCALIDAD ===
        "facturacion_montevideo_2025": {
            "patrones": ["facturación montevideo 2025", "facturamos montevideo", 
                        "ingresos montevideo 2025", "montevideo 2025 facturación"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2025 AND localidad = 'MONTEVIDEO'
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        "facturacion_mercedes_2025": {
            "patrones": ["facturación mercedes 2025", "facturamos mercedes", 
                        "ingresos mercedes 2025", "mercedes 2025 facturación"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'INGRESO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2025 AND localidad = 'MERCEDES'
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === POR ÁREA ===
        "facturacion_juridica_2025": {
            "patrones": ["facturación jurídica 2025", "jurídica 2025", 
                        "área jurídica 2025", "ingresos jurídica"],
            "sql_control": """
                SELECT SUM(o.monto_uyu) as total FROM operaciones o
                JOIN areas a ON o.area_id = a.id
                WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
                AND EXTRACT(YEAR FROM o.fecha) = 2025 AND a.nombre = 'Jurídica'
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        "facturacion_notarial_2025": {
            "patrones": ["facturación notarial 2025", "notarial 2025", 
                        "área notarial 2025", "ingresos notarial"],
            "sql_control": """
                SELECT SUM(o.monto_uyu) as total FROM operaciones o
                JOIN areas a ON o.area_id = a.id
                WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
                AND EXTRACT(YEAR FROM o.fecha) = 2025 AND a.nombre = 'Notarial'
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        "facturacion_contable_2025": {
            "patrones": ["facturación contable 2025", "contable 2025", 
                        "área contable 2025", "ingresos contable"],
            "sql_control": """
                SELECT SUM(o.monto_uyu) as total FROM operaciones o
                JOIN areas a ON o.area_id = a.id
                WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL 
                AND EXTRACT(YEAR FROM o.fecha) = 2025 AND a.nombre = 'Contable'
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === DISTRIBUCIONES ===
        "distribuciones_2025": {
            "patrones": ["distribuciones 2025", "distribuciones este año", 
                        "total distribuido 2025", "cuánto se distribuyó 2025"],
            "sql_control": """
                SELECT SUM(dd.monto_uyu) as total 
                FROM distribuciones_detalle dd
                JOIN operaciones o ON dd.operacion_id = o.id
                WHERE o.tipo_operacion = 'DISTRIBUCION' AND o.deleted_at IS NULL
                AND EXTRACT(YEAR FROM o.fecha) = 2025
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        "distribuciones_2024": {
            "patrones": ["distribuciones 2024", "total distribuido 2024", 
                        "cuánto se distribuyó 2024"],
            "sql_control": """
                SELECT SUM(dd.monto_uyu) as total 
                FROM distribuciones_detalle dd
                JOIN operaciones o ON dd.operacion_id = o.id
                WHERE o.tipo_operacion = 'DISTRIBUCION' AND o.deleted_at IS NULL
                AND EXTRACT(YEAR FROM o.fecha) = 2024
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === RETIROS ===
        "retiros_2025": {
            "patrones": ["retiros 2025", "retiros este año", "total retiros 2025"],
            "sql_control": """
                SELECT SUM(monto_uyu) as total FROM operaciones 
                WHERE tipo_operacion = 'RETIRO' AND deleted_at IS NULL 
                AND EXTRACT(YEAR FROM fecha) = 2025
            """,
            "campo_resultado": "total",
            "tolerancia": 0.01
        },
        
        # === OPERACIONES ===
        "cantidad_operaciones_2025": {
            "patrones": ["cuántas operaciones 2025", "operaciones este año", 
                        "cantidad operaciones 2025"],
            "sql_control": """
                SELECT COUNT(*) as total FROM operaciones 
                WHERE deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025
            """,
            "campo_resultado": "total",
            "tolerancia": 0  # Debe ser exacto
        },
    }
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE IDENTIFICACIÓN
    # ══════════════════════════════════════════════════════════════
    
    @classmethod
    def identificar_query_canonica(cls, pregunta: str) -> Optional[str]:
        """
        Identifica si la pregunta coincide con alguna query canónica.
        
        Args:
            pregunta: Pregunta del usuario
            
        Returns:
            Key de la query canónica o None si no coincide
        """
        pregunta_lower = pregunta.lower()
        
        for key, config in cls.QUERIES_CANONICAS.items():
            for patron in config["patrones"]:
                if patron in pregunta_lower:
                    logger.debug(f"Query canónica identificada: {key} (patrón: '{patron}')")
                    return key
        
        return None
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE EJECUCIÓN
    # ══════════════════════════════════════════════════════════════
    
    @classmethod
    def ejecutar_query_control(cls, db: Session, query_key: str) -> Optional[float]:
        """
        Ejecuta la query de control y retorna el resultado.
        
        Args:
            db: Sesión de base de datos
            query_key: Key de la query canónica
            
        Returns:
            Valor numérico resultado o None si falla
        """
        if query_key not in cls.QUERIES_CANONICAS:
            return None
        
        sql = cls.QUERIES_CANONICAS[query_key]["sql_control"]
        
        try:
            result = db.execute(text(sql)).fetchone()
            if result and result[0] is not None:
                return float(result[0])
            return 0.0  # Si es NULL, retornar 0
        except Exception as e:
            logger.error(f"Error ejecutando query de control '{query_key}': {e}")
            return None
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE EXTRACCIÓN
    # ══════════════════════════════════════════════════════════════
    
    @classmethod
    def extraer_valor_respuesta(cls, respuesta: str, datos_raw: Any) -> Optional[float]:
        """
        Extrae el valor numérico principal de la respuesta del CFO AI.
        
        Prioridad:
        1. datos_raw (más preciso)
        2. Texto de respuesta (regex)
        
        Args:
            respuesta: Texto de respuesta narrativa
            datos_raw: Datos crudos de la consulta SQL
            
        Returns:
            Valor numérico extraído o None
        """
        # 1. Intentar extraer de datos_raw primero (más preciso)
        if datos_raw:
            if isinstance(datos_raw, list) and len(datos_raw) > 0:
                primer_registro = datos_raw[0]
                if isinstance(primer_registro, dict):
                    # Buscar campos comunes en orden de prioridad
                    campos_prioritarios = [
                        'total', 'total_uyu', 'sum', 'monto', 'valor',
                        'rentabilidad', 'porcentaje', 'margen', 'ing', 'gas'
                    ]
                    for campo in campos_prioritarios:
                        if campo in primer_registro and primer_registro[campo] is not None:
                            try:
                                return float(primer_registro[campo])
                            except (ValueError, TypeError):
                                continue
        
        # 2. Intentar extraer del texto de respuesta usando regex
        patrones = [
            r'\$\s*([\d.,]+)',           # $12.340.660
            r'([\d.,]+)\s*%',            # 68,30%
            r'([\d.,]+)\s*UYU',          # 12340660 UYU
            r'([\d.,]+)\s*pesos',        # 12340660 pesos
            r'total[:\s]*([\d.,]+)',     # total: 12340660
        ]
        
        for patron in patrones:
            matches = re.findall(patron, respuesta, re.IGNORECASE)
            if matches:
                try:
                    # Limpiar y convertir (formato uruguayo: 1.234.567,89)
                    valor_str = matches[0]
                    # Si tiene más de un punto, es separador de miles
                    if valor_str.count('.') > 1:
                        valor_str = valor_str.replace('.', '')
                    elif ',' in valor_str:
                        valor_str = valor_str.replace('.', '').replace(',', '.')
                    return float(valor_str)
                except (ValueError, IndexError):
                    continue
        
        return None
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL DE VALIDACIÓN
    # ══════════════════════════════════════════════════════════════
    
    @classmethod
    def validar_respuesta(
        cls, 
        db: Session, 
        pregunta: str, 
        respuesta: str, 
        datos_raw: Any = None
    ) -> Dict[str, Any]:
        """
        Valida la respuesta del CFO AI contra query de control.
        
        Args:
            db: Sesión de base de datos
            pregunta: Pregunta original del usuario
            respuesta: Respuesta narrativa del CFO AI
            datos_raw: Datos crudos de la consulta
            
        Returns:
            Dict con resultado de validación:
            {
                "validado": bool - True si se pudo validar
                "query_canonica": str - Key de la query usada
                "valor_cfo": float - Valor extraído de CFO AI
                "valor_control": float - Valor de query de control
                "diferencia_porcentual": float - % de diferencia
                "dentro_tolerancia": bool - Si está dentro del margen
                "advertencia": str - Mensaje de advertencia si aplica
            }
        """
        resultado = {
            "validado": False,
            "query_canonica": None,
            "valor_cfo": None,
            "valor_control": None,
            "diferencia_porcentual": None,
            "dentro_tolerancia": None,
            "advertencia": None
        }
        
        # 1. Identificar si es una query canónica
        query_key = cls.identificar_query_canonica(pregunta)
        if not query_key:
            # No es una query canónica conocida - no validar
            return resultado
        
        resultado["query_canonica"] = query_key
        config = cls.QUERIES_CANONICAS[query_key]
        
        # 2. Ejecutar query de control
        valor_control = cls.ejecutar_query_control(db, query_key)
        if valor_control is None:
            logger.warning(f"Validación canónica: No se pudo ejecutar query de control para '{query_key}'")
            return resultado
        
        resultado["valor_control"] = valor_control
        
        # 3. Extraer valor de la respuesta del CFO
        valor_cfo = cls.extraer_valor_respuesta(respuesta, datos_raw)
        if valor_cfo is None:
            logger.warning(f"Validación canónica: No se pudo extraer valor de respuesta CFO para '{query_key}'")
            return resultado
        
        resultado["valor_cfo"] = valor_cfo
        resultado["validado"] = True
        
        # 4. Calcular diferencia porcentual
        if valor_control != 0:
            diferencia = abs(valor_cfo - valor_control) / abs(valor_control) * 100
        else:
            diferencia = 0.0 if valor_cfo == 0 else 100.0
        
        resultado["diferencia_porcentual"] = round(diferencia, 2)
        
        # 5. Verificar tolerancia
        tolerancia_pct = config["tolerancia"] * 100  # Convertir a porcentaje
        resultado["dentro_tolerancia"] = diferencia <= tolerancia_pct
        
        # 6. Generar advertencia si está fuera de tolerancia
        if not resultado["dentro_tolerancia"]:
            resultado["advertencia"] = (
                f"\n\n⚠️ **ADVERTENCIA DE PRECISIÓN**: La respuesta difiere **{diferencia:.2f}%** "
                f"del valor de control.\n"
                f"- Valor reportado: ${valor_cfo:,.0f}\n"
                f"- Valor de control: ${valor_control:,.0f}\n"
                f"- Query de validación: `{query_key}`"
            )
            logger.warning(
                f"Validación canónica FALLIDA [{query_key}]: "
                f"CFO=${valor_cfo:,.0f}, Control=${valor_control:,.0f}, "
                f"Diferencia={diferencia:.2f}% (tolerancia={tolerancia_pct}%)"
            )
        else:
            logger.info(
                f"Validación canónica OK [{query_key}]: "
                f"Diferencia={diferencia:.2f}% (tolerancia={tolerancia_pct}%)"
            )
        
        return resultado


# ══════════════════════════════════════════════════════════════
# FUNCIÓN DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════

def validar_respuesta_cfo(
    db: Session, 
    pregunta: str, 
    respuesta: str, 
    datos_raw: Any = None
) -> Dict[str, Any]:
    """
    Función wrapper para validar respuesta del CFO AI.
    
    Uso:
        from app.services.validador_canonico import validar_respuesta_cfo
        
        validacion = validar_respuesta_cfo(db, pregunta, respuesta, datos)
        if validacion.get('advertencia'):
            respuesta += validacion['advertencia']
    """
    return ValidadorCanonico.validar_respuesta(db, pregunta, respuesta, datos_raw)

