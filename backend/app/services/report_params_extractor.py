"""
Report Params Extractor - Sistema CFO Inteligente

Extrae parámetros estructurados de una solicitud de reporte usando Claude.
Convierte lenguaje natural en parámetros precisos para generar el PDF.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import json
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.logger import get_logger
from app.core.config import settings
from app.services.ai.ai_orchestrator import AIOrchestrator

logger = get_logger(__name__)


class ReportType(str, Enum):
    """Tipos de reporte soportados."""
    MENSUAL = "mensual"
    TRIMESTRAL = "trimestral"
    ANUAL = "anual"
    COMPARATIVO = "comparativo"
    POR_AREA = "por_area"
    POR_LOCALIDAD = "por_localidad"
    POR_SOCIO = "por_socio"
    EJECUTIVO = "ejecutivo"
    GENERAL = "general"


@dataclass
class PeriodoReporte:
    """Representa un período de tiempo para el reporte."""
    fecha_inicio: date
    fecha_fin: date
    label: str  # "Noviembre 2024", "Q1 2025", etc.


@dataclass
class ReportParams:
    """Parámetros extraídos para generar un reporte."""
    tipo: ReportType
    titulo: str
    periodo_actual: PeriodoReporte
    periodo_comparacion: Optional[PeriodoReporte]
    dimensiones: List[str]  # ["area", "localidad", "socio"]
    moneda_preferida: str  # "UYU" o "USD"
    incluir_graficos: bool
    incluir_narrativas_ia: bool
    filtros_adicionales: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            "tipo": self.tipo.value,
            "titulo": self.titulo,
            "periodo_actual": {
                "fecha_inicio": self.periodo_actual.fecha_inicio.isoformat(),
                "fecha_fin": self.periodo_actual.fecha_fin.isoformat(),
                "label": self.periodo_actual.label
            },
            "periodo_comparacion": {
                "fecha_inicio": self.periodo_comparacion.fecha_inicio.isoformat(),
                "fecha_fin": self.periodo_comparacion.fecha_fin.isoformat(),
                "label": self.periodo_comparacion.label
            } if self.periodo_comparacion else None,
            "dimensiones": self.dimensiones,
            "moneda_preferida": self.moneda_preferida,
            "incluir_graficos": self.incluir_graficos,
            "incluir_narrativas_ia": self.incluir_narrativas_ia,
            "filtros_adicionales": self.filtros_adicionales
        }


class ReportParamsExtractor:
    """
    Extrae parámetros estructurados de una solicitud de reporte.
    
    Usa Claude para interpretar lenguaje natural y convertirlo en
    parámetros precisos para el generador de PDF.
    
    Ejemplo:
        >>> extractor = ReportParamsExtractor()
        >>> params = extractor.extract("Genera reporte comparativo Nov 2024 vs Nov 2023")
        >>> params.tipo
        ReportType.COMPARATIVO
        >>> params.periodo_actual.label
        "Noviembre 2024"
    """
    
    EXTRACTION_PROMPT = """Eres un asistente que extrae parámetros de solicitudes de reportes financieros.

CONTEXTO:
- Sistema CFO de Conexión Consultora (firma legal-contable uruguaya)
- Fecha actual: {fecha_actual}
- Datos disponibles desde: 2024-01-01 hasta hoy
- Localidades: Montevideo, Mercedes
- Áreas: Jurídica, Notarial, Contable, Recuperación, Gastos Generales, Otros
- Socios: Agustina, Viviana, Gonzalo, Pancho, Bruno

SOLICITUD DEL USUARIO:
"{pregunta}"

EXTRAE los siguientes parámetros en formato JSON:

{{
    "tipo_reporte": "mensual|trimestral|anual|comparativo|por_area|por_localidad|por_socio|ejecutivo|general",
    "titulo_sugerido": "Título descriptivo del reporte",
    "periodo_actual": {{
        "fecha_inicio": "YYYY-MM-DD",
        "fecha_fin": "YYYY-MM-DD",
        "label": "Nombre legible del período (ej: Noviembre 2024, Q1 2025)"
    }},
    "periodo_comparacion": {{
        "fecha_inicio": "YYYY-MM-DD",
        "fecha_fin": "YYYY-MM-DD",
        "label": "Nombre del período de comparación"
    }} o null si no hay comparación,
    "dimensiones": ["area", "localidad", "socio"] - cuáles incluir,
    "moneda": "UYU" o "USD",
    "incluir_graficos": true/false,
    "incluir_narrativas": true/false,
    "filtros": {{}} - filtros específicos si los menciona
}}

REGLAS:
1. Si dice "este mes" sin año → usar {mes_actual} {anio_actual}
2. Si dice "mes pasado" → calcular mes anterior
3. Si dice "Q1/Q2/Q3/Q4" → calcular fechas del trimestre
4. Si dice "comparativo/vs/versus" → incluir periodo_comparacion
5. Si menciona área/localidad/socio específico → agregar en filtros
6. Si dice "ejecutivo" o "para directorio" → tipo ejecutivo con narrativas
7. Default: incluir_graficos=true, incluir_narrativas=true, moneda=UYU

Responde SOLO con el JSON, sin explicaciones adicionales."""

    def __init__(self):
        """Inicializa el extractor con el orquestador de IA."""
        self._orchestrator = AIOrchestrator()
        self._hoy = date.today()
        logger.info("ReportParamsExtractor inicializado")
    
    def _get_prompt(self, pregunta: str) -> str:
        """Construye el prompt con fecha actual."""
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        return self.EXTRACTION_PROMPT.format(
            fecha_actual=self._hoy.isoformat(),
            mes_actual=meses[self._hoy.month - 1],
            anio_actual=self._hoy.year,
            pregunta=pregunta
        )
    
    def _parse_date(self, date_str: str) -> date:
        """Parsea fecha desde string ISO."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            logger.warning(f"No se pudo parsear fecha: {date_str}, usando hoy")
            return self._hoy
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parsea la respuesta JSON de Claude."""
        # Limpiar respuesta si viene con markdown
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remover backticks de markdown
            lines = cleaned.split("\n")
            # Filtrar líneas que son solo backticks o json
            filtered = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(filtered).strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            logger.debug(f"Respuesta raw: {response[:500]}")
            return {}
    
    def _build_params(self, data: Dict[str, Any], pregunta: str) -> ReportParams:
        """Construye ReportParams desde el diccionario extraído."""
        
        # Tipo de reporte
        tipo_str = data.get("tipo_reporte", "general")
        try:
            tipo = ReportType(tipo_str)
        except ValueError:
            tipo = ReportType.GENERAL
        
        # Período actual
        periodo_actual_data = data.get("periodo_actual", {})
        periodo_actual = PeriodoReporte(
            fecha_inicio=self._parse_date(periodo_actual_data.get("fecha_inicio", self._hoy.replace(day=1).isoformat())),
            fecha_fin=self._parse_date(periodo_actual_data.get("fecha_fin", self._hoy.isoformat())),
            label=periodo_actual_data.get("label", f"{self._hoy.strftime('%B %Y')}")
        )
        
        # Período de comparación (opcional)
        periodo_comp_data = data.get("periodo_comparacion")
        periodo_comparacion = None
        if periodo_comp_data:
            periodo_comparacion = PeriodoReporte(
                fecha_inicio=self._parse_date(periodo_comp_data.get("fecha_inicio")),
                fecha_fin=self._parse_date(periodo_comp_data.get("fecha_fin")),
                label=periodo_comp_data.get("label", "Período anterior")
            )
        
        # Construir parámetros
        return ReportParams(
            tipo=tipo,
            titulo=data.get("titulo_sugerido", f"Reporte {tipo.value.title()}"),
            periodo_actual=periodo_actual,
            periodo_comparacion=periodo_comparacion,
            dimensiones=data.get("dimensiones", ["area"]),
            moneda_preferida=data.get("moneda", "UYU"),
            incluir_graficos=data.get("incluir_graficos", True),
            incluir_narrativas_ia=data.get("incluir_narrativas", True),
            filtros_adicionales=data.get("filtros", {})
        )
    
    def _get_fallback_params(self, pregunta: str) -> ReportParams:
        """Genera parámetros por defecto si falla la extracción."""
        # Primer día del mes actual
        primer_dia = self._hoy.replace(day=1)
        
        # Detectar tipo básico
        pregunta_lower = pregunta.lower()
        if "comparativo" in pregunta_lower or "vs" in pregunta_lower:
            tipo = ReportType.COMPARATIVO
        elif "área" in pregunta_lower or "areas" in pregunta_lower:
            tipo = ReportType.POR_AREA
        elif "localidad" in pregunta_lower or "montevideo" in pregunta_lower or "mercedes" in pregunta_lower:
            tipo = ReportType.POR_LOCALIDAD
        elif "ejecutivo" in pregunta_lower:
            tipo = ReportType.EJECUTIVO
        else:
            tipo = ReportType.MENSUAL
        
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        return ReportParams(
            tipo=tipo,
            titulo=f"Reporte {tipo.value.title()} - {meses[self._hoy.month - 1]} {self._hoy.year}",
            periodo_actual=PeriodoReporte(
                fecha_inicio=primer_dia,
                fecha_fin=self._hoy,
                label=f"{meses[self._hoy.month - 1]} {self._hoy.year}"
            ),
            periodo_comparacion=None,
            dimensiones=["area"],
            moneda_preferida="UYU",
            incluir_graficos=True,
            incluir_narrativas_ia=True,
            filtros_adicionales={}
        )
    
    def extract(self, pregunta: str) -> ReportParams:
        """
        Extrae parámetros de una solicitud de reporte.
        
        Args:
            pregunta: Solicitud del usuario en lenguaje natural
            
        Returns:
            ReportParams con los parámetros extraídos
        """
        logger.info(f"Extrayendo parámetros de: '{pregunta[:60]}...'")
        
        try:
            # Construir prompt
            prompt = self._get_prompt(pregunta)
            
            # Llamar a Claude
            response = self._orchestrator.complete(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1  # Baja temperatura para respuestas consistentes
            )
            
            if not response:
                logger.warning("Respuesta vacía de IA, usando fallback")
                return self._get_fallback_params(pregunta)
            
            # Parsear respuesta
            data = self._parse_response(response)
            
            if not data:
                logger.warning("No se pudo parsear respuesta, usando fallback")
                return self._get_fallback_params(pregunta)
            
            # Construir parámetros
            params = self._build_params(data, pregunta)
            
            logger.info(f"Parámetros extraídos: tipo={params.tipo.value}, "
                       f"periodo={params.periodo_actual.label}, "
                       f"comparacion={'Sí' if params.periodo_comparacion else 'No'}")
            
            return params
            
        except Exception as e:
            logger.error(f"Error extrayendo parámetros: {type(e).__name__}: {e}")
            return self._get_fallback_params(pregunta)
    
    def extract_to_dict(self, pregunta: str) -> Dict[str, Any]:
        """
        Extrae parámetros y retorna como diccionario.
        
        Útil para serialización JSON o logging.
        """
        params = self.extract(pregunta)
        return params.to_dict()


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN HELPER
# ═══════════════════════════════════════════════════════════════════════════

def extract_report_params(pregunta: str) -> Dict[str, Any]:
    """
    Función simple para extraer parámetros de reporte.
    
    Args:
        pregunta: Solicitud del usuario
        
    Returns:
        Dict con parámetros estructurados
    """
    extractor = ReportParamsExtractor()
    return extractor.extract_to_dict(pregunta)


# ═══════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════

def _run_tests():
    """Tests del extractor de parámetros."""
    
    casos_test = [
        "Genera un reporte de noviembre 2024",
        "Dame un PDF comparativo Q1 2024 vs Q1 2025",
        "Quiero un informe de rentabilidad por área",
        "Reporte ejecutivo del primer semestre 2024 para el directorio",
        "Análisis comparativo Montevideo vs Mercedes este mes",
        "Reporte mensual de diciembre con gráficos",
    ]
    
    print("\n" + "="*70)
    print(" TEST DE EXTRACCIÓN DE PARÁMETROS")
    print("="*70)
    
    extractor = ReportParamsExtractor()
    
    for caso in casos_test:
        print(f"\n📝 Solicitud: {caso}")
        print("-" * 50)
        
        try:
            params = extractor.extract(caso)
            print(f"   Tipo: {params.tipo.value}")
            print(f"   Título: {params.titulo}")
            print(f"   Período: {params.periodo_actual.label}")
            print(f"   Comparación: {params.periodo_comparacion.label if params.periodo_comparacion else 'No'}")
            print(f"   Dimensiones: {params.dimensiones}")
            print(f"   Moneda: {params.moneda_preferida}")
            print(f"   Gráficos: {params.incluir_graficos}")
            print(f"   Narrativas IA: {params.incluir_narrativas_ia}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    _run_tests()

