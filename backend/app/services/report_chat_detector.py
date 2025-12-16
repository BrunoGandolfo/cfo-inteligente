"""
Report Chat Detector - Sistema CFO Inteligente

Detecta si una pregunta del usuario es una solicitud de reporte/PDF.
Implementación basada en keywords y regex, sin dependencias de IA.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import re
from typing import Tuple, Dict, Any, List
from dataclasses import dataclass

from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionResult:
    """Resultado de la detección de solicitud de reporte."""
    is_report: bool
    confidence: float
    type_hint: str
    reason: str


class ReportRequestDetector:
    """
    Detecta si una pregunta del usuario es una solicitud de reporte/PDF.
    
    Ejemplos que DEBEN detectarse como reporte:
    - "Genera un reporte de noviembre 2024"
    - "Dame un PDF comparativo Q1 2024 vs Q1 2025"
    - "Quiero un informe de rentabilidad por área"
    - "Necesito un análisis detallado del primer semestre"
    - "Exporta a PDF el resumen del año"
    - "Preparame un reporte ejecutivo de este mes"
    
    Ejemplos que NO son reportes (preguntas normales):
    - "¿Cuánto facturamos en noviembre?"
    - "¿Cuál es la rentabilidad del área jurídica?"
    - "¿Cómo estamos comparado con el año pasado?"
    """
    
    # Umbral de confianza para considerar como reporte
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self):
        # Palabras clave primarias (alta probabilidad) - peso 0.4
        self.keywords_primarias: List[str] = [
            "reporte", "informe", "pdf", "exporta", "exportar",
            "documento", "análisis detallado", "análisis completo"
        ]
        
        # Verbos de acción que indican generación - peso 0.3
        self.verbos_generacion: List[str] = [
            "genera", "generar", "generame", "preparame", "preparar",
            "hazme", "haceme", "creame", "crear", "dame", "envíame",
            "mándame", "necesito", "quiero", "quisiera", "podrías"
        ]
        
        # Palabras clave secundarias (requieren contexto) - peso 0.2
        self.keywords_secundarias: List[str] = [
            "detallado", "completo", "ejecutivo", "profesional",
            "para presentar", "para el directorio", "para los socios",
            "formal", "imprimible", "descargable"
        ]
        
        # Modificadores de tipo de reporte - peso 0.1
        self.modificadores_tipo: Dict[str, List[str]] = {
            "comparativo": ["comparativo", "comparar", "versus", "vs", "contra", "comparación"],
            "mensual": ["mensual", "del mes", "este mes", "mes pasado", "mes anterior"],
            "trimestral": ["trimestral", "trimestre", "q1", "q2", "q3", "q4"],
            "anual": ["anual", "del año", "este año", "año pasado", "ytd"],
            "por_area": ["por área", "por áreas", "desglose área", "cada área"],
            "por_localidad": ["por localidad", "montevideo", "mercedes", "por oficina"],
            "ejecutivo": ["ejecutivo", "resumen ejecutivo", "para gerencia", "directorio"]
        }
        
        # Patrones regex para detectar solicitudes (ordenados por especificidad)
        self.patterns: List[Tuple[str, float]] = [
            # Muy específicos - alta confianza
            (r"(?:genera|dame|preparame|hazme|creame)\s+(?:un|el)?\s*(?:reporte|informe|pdf)", 0.9),
            (r"exporta(?:r|me)?\s+(?:a\s+)?pdf", 0.9),
            (r"(?:necesito|quiero)\s+(?:un|el)?\s*(?:reporte|informe|documento)", 0.85),
            (r"(?:reporte|informe)\s+(?:ejecutivo|comparativo|detallado|completo)", 0.85),
            
            # Específicos - confianza media-alta
            (r"(?:reporte|informe)\s+(?:de|del|para)\s+\w+", 0.75),
            (r"análisis\s+(?:detallado|completo|profundo)", 0.7),
            (r"(?:pdf|documento)\s+(?:con|de|del)", 0.7),
            
            # Genéricos - requieren más contexto
            (r"(?:genera|preparame)\s+(?:un|el)?\s*análisis", 0.6),
        ]
        
        # Palabras que REDUCEN la probabilidad de ser reporte
        self.negative_indicators: List[str] = [
            "cuánto", "cuanto", "cuál", "cual", "cómo", "como", 
            "por qué", "porque", "qué es", "que es", "dime",
            "explica", "explicame", "?",
        ]
    
    def _normalize(self, text: str) -> str:
        """Normaliza texto para comparación."""
        return text.lower().strip()
    
    def _count_keyword_matches(self, pregunta: str, keywords: List[str]) -> int:
        """Cuenta cuántas keywords coinciden."""
        pregunta_lower = self._normalize(pregunta)
        return sum(1 for kw in keywords if kw.lower() in pregunta_lower)
    
    def _check_patterns(self, pregunta: str) -> Tuple[bool, float, str]:
        """Verifica patrones regex y retorna el de mayor confianza."""
        pregunta_lower = self._normalize(pregunta)
        best_match = (False, 0.0, "")
        
        for pattern, confidence in self.patterns:
            if re.search(pattern, pregunta_lower, re.IGNORECASE):
                if confidence > best_match[1]:
                    best_match = (True, confidence, f"Patrón: {pattern[:30]}...")
        
        return best_match
    
    def _has_negative_indicators(self, pregunta: str) -> bool:
        """Verifica si hay indicadores de pregunta normal (no reporte)."""
        pregunta_lower = self._normalize(pregunta)
        
        # Si es una pregunta directa (termina en ?)
        if pregunta.strip().endswith("?"):
            return True
        
        # Si comienza con palabra interrogativa
        for neg in self.negative_indicators:
            if pregunta_lower.startswith(neg) or f" {neg} " in pregunta_lower:
                return True
        
        return False
    
    def is_report_request(self, pregunta: str) -> Tuple[bool, float, str]:
        """
        Analiza si la pregunta es una solicitud de reporte.
        
        Args:
            pregunta: Texto de la pregunta del usuario
            
        Returns:
            tuple: (es_reporte: bool, confianza: float 0-1, razon: str)
        """
        if not pregunta or len(pregunta) < 5:
            return (False, 0.0, "Pregunta muy corta")
        
        pregunta_lower = self._normalize(pregunta)
        confidence = 0.0
        reasons = []
        
        # 1. Verificar patrones regex (más peso)
        pattern_match, pattern_conf, pattern_reason = self._check_patterns(pregunta)
        if pattern_match:
            confidence = max(confidence, pattern_conf)
            reasons.append(pattern_reason)
        
        # 2. Contar keywords primarias (peso 0.4 cada una, max 0.8)
        primary_matches = self._count_keyword_matches(pregunta, self.keywords_primarias)
        if primary_matches > 0:
            primary_score = min(primary_matches * 0.4, 0.8)
            confidence = max(confidence, primary_score)
            reasons.append(f"Keywords primarias: {primary_matches}")
        
        # 3. Contar verbos de generación (peso 0.3)
        verb_matches = self._count_keyword_matches(pregunta, self.verbos_generacion)
        if verb_matches > 0 and primary_matches > 0:
            # Solo suma si hay keyword primaria
            confidence = min(confidence + 0.3, 1.0)
            reasons.append(f"Verbos generación: {verb_matches}")
        
        # 4. Contar keywords secundarias (peso 0.15 cada una, max 0.3)
        secondary_matches = self._count_keyword_matches(pregunta, self.keywords_secundarias)
        if secondary_matches > 0:
            secondary_score = min(secondary_matches * 0.15, 0.3)
            confidence = min(confidence + secondary_score, 1.0)
            reasons.append(f"Keywords secundarias: {secondary_matches}")
        
        # 5. Penalizar si tiene indicadores negativos
        if self._has_negative_indicators(pregunta):
            confidence *= 0.5  # Reducir a la mitad
            reasons.append("Indicadores negativos detectados")
        
        # Determinar resultado
        is_report = confidence >= self.CONFIDENCE_THRESHOLD
        reason = " | ".join(reasons) if reasons else "Sin coincidencias"
        
        logger.debug(f"Detección reporte: '{pregunta[:50]}...' → {is_report} ({confidence:.2f}) - {reason}")
        
        return (is_report, round(confidence, 2), reason)
    
    def get_report_type_hint(self, pregunta: str) -> str:
        """
        Si es reporte, sugiere el tipo probable.
        
        Args:
            pregunta: Texto de la pregunta
            
        Returns:
            str: "comparativo", "mensual", "trimestral", "anual", 
                 "por_area", "por_localidad", "ejecutivo", "general"
        """
        pregunta_lower = self._normalize(pregunta)
        
        # Buscar en modificadores de tipo
        for tipo, keywords in self.modificadores_tipo.items():
            for kw in keywords:
                if kw.lower() in pregunta_lower:
                    return tipo
        
        # Si no se detecta tipo específico
        return "general"
    
    def extract_period_hints(self, pregunta: str) -> Dict[str, Any]:
        """
        Extrae pistas sobre el período solicitado.
        
        Returns:
            Dict con hints sobre el período (para que Claude los interprete)
        """
        pregunta_lower = self._normalize(pregunta)
        hints = {
            "raw_text": pregunta,
            "mentions_comparison": False,
            "period_keywords": [],
            "year_mentions": [],
            "month_mentions": []
        }
        
        # Detectar comparación
        comparison_words = ["vs", "versus", "contra", "comparar", "comparativo", "comparación"]
        if any(cw in pregunta_lower for cw in comparison_words):
            hints["mentions_comparison"] = True
        
        # Detectar años
        years = re.findall(r'20[0-9]{2}', pregunta)
        hints["year_mentions"] = list(set(years))
        
        # Detectar meses
        meses = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        for mes, num in meses.items():
            if mes in pregunta_lower:
                hints["month_mentions"].append({"name": mes, "number": num})
        
        # Detectar trimestres
        trimestres = re.findall(r'q[1-4]|primer(?:o)?\s+trimestre|segundo\s+trimestre|tercer(?:o)?\s+trimestre|cuarto\s+trimestre', pregunta_lower)
        if trimestres:
            hints["period_keywords"].extend(trimestres)
        
        return hints


def detect_report_request(pregunta: str) -> Dict[str, Any]:
    """
    Función simple para detectar solicitud de reporte.
    
    Args:
        pregunta: Texto de la pregunta del usuario
        
    Returns:
        {
            "is_report": bool,
            "confidence": float,
            "type_hint": str | None,
            "reason": str,
            "period_hints": dict | None
        }
    """
    detector = ReportRequestDetector()
    is_report, confidence, reason = detector.is_report_request(pregunta)
    
    result = {
        "is_report": is_report,
        "confidence": confidence,
        "type_hint": detector.get_report_type_hint(pregunta) if is_report else None,
        "reason": reason,
        "period_hints": detector.extract_period_hints(pregunta) if is_report else None
    }
    
    logger.info(f"Report detection: is_report={is_report}, confidence={confidence}, type={result.get('type_hint')}")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# TESTS (ejecutar con: python -m app.services.report_chat_detector)
# ═══════════════════════════════════════════════════════════════════════════

def _run_tests():
    """Tests de la detección de reportes."""
    
    # Casos que DEBEN ser reportes (confianza >= 0.7)
    casos_reporte = [
        "Genera un reporte de noviembre 2024",
        "Dame un PDF comparativo Q1 2024 vs Q1 2025",
        "Quiero un informe de rentabilidad por área",
        "Necesito un análisis detallado del primer semestre",
        "Exporta a PDF el resumen del año",
        "Preparame un reporte ejecutivo de este mes",
        "Hazme un informe comparativo Montevideo vs Mercedes",
        "Generame el reporte mensual de diciembre",
        "Necesito el PDF con el análisis de gastos",
        "Creame un documento con la rentabilidad por área",
    ]
    
    # Casos que NO deben ser reportes (confianza < 0.7)
    casos_no_reporte = [
        "¿Cuánto facturamos en noviembre?",
        "¿Cuál es la rentabilidad del área jurídica?",
        "¿Cómo estamos comparado con el año pasado?",
        "Dime los gastos de este mes",
        "¿Qué cliente facturó más?",
        "Explícame la diferencia entre retiro y distribución",
        "¿Por qué bajaron los ingresos?",
        "¿Cuántas operaciones hay en Mercedes?",
    ]
    
    detector = ReportRequestDetector()
    
    print("\n" + "="*70)
    print(" TESTS DE DETECCIÓN DE REPORTES")
    print("="*70)
    
    # Test casos reporte
    print("\n✅ CASOS QUE DEBEN SER REPORTES (>= 0.7):\n")
    errores_reporte = 0
    for caso in casos_reporte:
        is_report, conf, reason = detector.is_report_request(caso)
        status = "✅" if is_report else "❌"
        if not is_report:
            errores_reporte += 1
        print(f"{status} [{conf:.2f}] {caso[:50]}")
        if not is_report:
            print(f"   ⚠️  Razón: {reason}")
    
    # Test casos no reporte
    print("\n❌ CASOS QUE NO DEBEN SER REPORTES (< 0.7):\n")
    errores_no_reporte = 0
    for caso in casos_no_reporte:
        is_report, conf, reason = detector.is_report_request(caso)
        status = "✅" if not is_report else "❌"
        if is_report:
            errores_no_reporte += 1
        print(f"{status} [{conf:.2f}] {caso[:50]}")
        if is_report:
            print(f"   ⚠️  Falso positivo: {reason}")
    
    # Resumen
    print("\n" + "="*70)
    total_tests = len(casos_reporte) + len(casos_no_reporte)
    total_errores = errores_reporte + errores_no_reporte
    print(f" RESULTADO: {total_tests - total_errores}/{total_tests} tests pasados")
    print(f"   - Falsos negativos (debían ser reporte): {errores_reporte}")
    print(f"   - Falsos positivos (no debían ser reporte): {errores_no_reporte}")
    print("="*70 + "\n")
    
    # Test de tipos
    print("\n📊 TEST DE DETECCIÓN DE TIPOS:\n")
    casos_tipo = [
        ("Reporte comparativo Q1 vs Q2", "comparativo"),
        ("Informe mensual de diciembre", "mensual"),
        ("Análisis trimestral Q3 2024", "trimestral"),
        ("Reporte anual 2024", "anual"),
        ("Informe por área de ingresos", "por_area"),
        ("Reporte ejecutivo para directorio", "ejecutivo"),
    ]
    for caso, tipo_esperado in casos_tipo:
        tipo_detectado = detector.get_report_type_hint(caso)
        status = "✅" if tipo_detectado == tipo_esperado else "❌"
        print(f"{status} '{caso[:40]}' → {tipo_detectado} (esperado: {tipo_esperado})")
    
    return total_errores == 0


if __name__ == "__main__":
    _run_tests()

