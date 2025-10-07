"""
InsightGenerator - Genera insights usando Claude Sonnet 4.5

Integra con Claude API para generar análisis inteligentes y variados.
Usa temperatura controlada (0.2-0.3) para variabilidad sin sacrificar calidad.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

import anthropic
import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

from app.core.logger import get_logger
from app.core.constants import CLAUDE_MODEL

load_dotenv()

logger = get_logger(__name__)


class InsightGenerator:
    """
    Generador de insights financieros usando Claude Sonnet 4.5.
    
    Características:
    - Temperatura 0.2-0.3 para variabilidad controlada
    - Fuerza respuesta JSON estructurada
    - Manejo robusto de errores
    - Fallback a insights básicos si Claude falla
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en .env")
        
        self.client = anthropic.Anthropic(api_key=api_key.strip())
    
    def generate_insights(
        self, 
        context_string: str,
        num_insights: int = 4,
        temperature: float = 0.2
    ) -> List[Dict[str, str]]:
        """
        Genera insights usando Claude Sonnet 4.5.
        
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
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            insights_text = response.content[0].text.strip()
            
            # Parsear JSON
            insights = self._parse_insights(insights_text)
            
            logger.info(f"Insights generados exitosamente: {len(insights)} items")
            
            return insights
        
        except Exception as e:
            logger.error(f"Error generando insights: {e}", exc_info=True)
            return self._generate_fallback_insights(context_string)
    
    def _build_prompt(self, context_string: str, num_insights: int) -> str:
        """Construye prompt para Claude"""
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

TIPOS DE INSIGHTS (variar):
- tendencia: Patrones de crecimiento/decrecimiento
- alerta: Situaciones que requieren atención
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
        """Parsea respuesta de Claude a JSON"""
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
        """Genera insights básicos si Claude falla"""
        logger.warning("Usando insights fallback (Claude falló)")
        
        return [
            {
                'tipo': 'destacado',
                'titulo': 'Datos del período',
                'descripcion': 'El análisis detallado no está disponible temporalmente. Consulte las métricas numéricas en el reporte.',
                'relevancia': 'media'
            }
        ]

