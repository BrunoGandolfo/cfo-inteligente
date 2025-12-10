"""
InsightGenerator - Genera insights usando IA con fallback multi-proveedor

Usa AIOrchestrator para fallback automático: Claude → OpenAI → Gemini
Usa temperatura controlada (0.2-0.3) para variabilidad sin sacrificar calidad.

Autor: Sistema CFO Inteligente
Fecha: Diciembre 2025
"""

import json
from typing import Dict, Any, List

from app.core.logger import get_logger
from app.services.ai.ai_orchestrator import AIOrchestrator

logger = get_logger(__name__)


class InsightGenerator:
    """
    Generador de insights financieros con fallback multi-proveedor.
    
    Características:
    - Temperatura 0.2-0.3 para variabilidad controlada
    - Fuerza respuesta JSON estructurada
    - Manejo robusto de errores
    - Fallback automático: Claude → OpenAI → Gemini
    - Fallback a insights básicos si todos los proveedores fallan
    """
    
    def __init__(self):
        self._orchestrator = AIOrchestrator()
        logger.info("InsightGenerator inicializado con AIOrchestrator")
    
    def generate_insights(
        self, 
        context_string: str,
        num_insights: int = 4,
        temperature: float = 0.2
    ) -> List[Dict[str, str]]:
        """
        Genera insights usando IA con fallback multi-proveedor.
        
        Args:
            context_string: Contexto formateado con métricas e histórico
            num_insights: Número de insights a generar (3-5 recomendado)
            temperature: 0.0-1.0, recomendado 0.2-0.3 para variabilidad
            
        Returns:
            Lista de insights estructurados:
            [
                {
                    'tipo': 'tendencia' | 'alerta' | 'destacado' | 'oportunidad',
                    'titulo': 'Título breve',
                    'descripcion': 'Análisis detallado con números',
                    'relevancia': 'alta' | 'media' | 'baja'
                }
            ]
        """
        logger.info(f"Generando {num_insights} insights con temperatura {temperature}")
        
        prompt = self._build_prompt(context_string, num_insights)
        
        try:
            # Usar AIOrchestrator con fallback automático
            insights_text = self._orchestrator.complete(
                prompt=prompt,
                max_tokens=2000,
                temperature=temperature
            )
            
            if not insights_text:
                logger.warning("AIOrchestrator retornó None - usando fallback")
                return self._generate_fallback_insights(context_string)
            
            # Parsear JSON
            insights = self._parse_insights(insights_text)
            
            logger.info(f"Insights generados exitosamente: {len(insights)} items")
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generando insights: {e}", exc_info=True)
            return self._generate_fallback_insights(context_string)
    
    def _build_prompt(self, context_string: str, num_insights: int) -> str:
        """Construye prompt para IA"""
        return f"""Eres un analista financiero senior de Conexión Consultora.

{context_string}

TAREA:
Genera EXACTAMENTE {num_insights} insights financieros para el reporte ejecutivo.

REGLAS CRÍTICAS:
1. Cada insight debe ser ESPECÍFICO con números concretos
2. NO uses frases genéricas como "los ingresos fueron buenos"
3. IDENTIFICA patrones NO obvios
4. COMPARA con histórico cuando sea relevante
5. SÉ preciso: "aumentó 23%" mejor que "aumentó considerablemente"
6. VARÍA el lenguaje: no repitas estructuras de frases
7. PRIORIZA insights accionables
8. USA EXACTAMENTE los valores proporcionados, NO recalcules ni estimes
9. ANTES de generar alertas sobre umbrales, VERIFICA los valores reales del período
10. NO generes alertas hipotéticas si los datos reales no las justifican
11. Si el Ratio Distribución/Utilidad es menor a 50%, NO alertes sobre descapitalización

TIPOS DE INSIGHTS (variar):
- tendencia: Patrones de crecimiento/decrecimiento
- alerta: Situaciones que requieren atención (SOLO si datos lo justifican)
- destacado: Logros o hitos significativos
- oportunidad: Áreas de mejora identificadas

FORMATO DE SALIDA (JSON estricto):
```json
[
    {{
        "tipo": "tendencia",
        "titulo": "Aceleración sostenida en Mercedes",
        "descripcion": "Mercedes registra 3 meses consecutivos de crecimiento (+15% promedio mensual), pasando de $45M en agosto a $62M en octubre. Esta tendencia sugiere consolidación del mercado regional.",
        "relevancia": "alta"
    }},
    ...
]
```

GENERA {num_insights} INSIGHTS AHORA (solo JSON, sin texto adicional):"""
    
    def _parse_insights(self, text: str) -> List[Dict[str, str]]:
        """Parsea respuesta de IA a JSON"""
        # Limpiar markdown si existe
        text = text.replace("```json", "").replace("```", "").strip()
        
        try:
            insights = json.loads(text)
            
            # Validar estructura
            if not isinstance(insights, list):
                raise ValueError("Insights debe ser una lista")
            
            for insight in insights:
                required_keys = ['tipo', 'titulo', 'descripcion', 'relevancia']
                if not all(k in insight for k in required_keys):
                    raise ValueError(f"Insight falta campos requeridos: {insight}")
            
            return insights
        
        except Exception as e:
            logger.error(f"Error parseando insights: {e}")
            raise
    
    def _generate_fallback_insights(self, context_string: str) -> List[Dict[str, str]]:
        """Genera insights básicos si todos los proveedores de IA fallan"""
        logger.warning("Usando insights fallback (todos los proveedores fallaron)")
        
        return [
            {
                'tipo': 'destacado',
                'titulo': 'Datos del período',
                'descripcion': 'El análisis detallado no está disponible temporalmente. Consulte las métricas numéricas en el reporte.',
                'relevancia': 'media'
            }
        ]
