"""
AnalysisLenses - Diferentes perspectivas analíticas para insights

Define 12+ "lentes" de análisis que rotan según el período para evitar repetitividad.
Cada lente enfoca el análisis desde un ángulo diferente.

Autor: Sistema CFO Inteligente  
Fecha: Octubre 2025
"""

from typing import List, Dict, Any
from datetime import date


class AnalysisLenses:
    """
    Gestiona las diferentes perspectivas analíticas para generar insights variados.
    
    Lentes disponibles:
    1. Crecimiento: Comparaciones MoM, YoY, tendencias
    2. Eficiencia: Rentabilidad, costos, optimización
    3. Concentración: Dependencia de clientes/áreas
    4. Riesgo: Volatilidad, outliers, anomalías
    5. Geográfico: Distribución Montevideo/Mercedes
    6. Temporal: Estacionalidad, ciclos
    7. Comparativo: Benchmarks, mejores prácticas
    8. Proyectivo: Forecasts, escenarios
    9. Operativo: Eficiencia diaria, productividad
    10. Estratégico: Posicionamiento, oportunidades
    11. Financiero: Liquidez, solvencia
    12. Competitivo: Market share (si aplica)
    """
    
    # Definición de lentes con sus prompts característicos
    LENSES = {
        'crecimiento': {
            'nombre': 'Análisis de Crecimiento',
            'keywords': ['crecer', 'aumentar', 'expandir', 'tendencia alcista', 'momentum'],
            'prompt_fragment': """
Enfócate en:
- Tasas de crecimiento (MoM, YoY)
- Aceleración o desaceleración
- Drivers del crecimiento
- Sostenibilidad de la tendencia
"""
        },
        'eficiencia': {
            'nombre': 'Análisis de Eficiencia Operativa',
            'keywords': ['rentabilidad', 'margen', 'optimizar', 'eficiencia', 'productividad'],
            'prompt_fragment': """
Enfócate en:
- Evolución de márgenes
- Relación ingresos/gastos
- Áreas más/menos eficientes
- Oportunidades de optimización
"""
        },
        'concentracion': {
            'nombre': 'Análisis de Concentración de Riesgos',
            'keywords': ['dependencia', 'concentración', 'diversificación', 'distribución'],
            'prompt_fragment': """
Enfócate en:
- % que representa área/cliente principal
- Distribución de ingresos
- Riesgos de concentración
- Nivel de diversificación
"""
        },
        'anomalias': {
            'nombre': 'Detección de Anomalías',
            'keywords': ['inusual', 'atípico', 'outlier', 'excepción', 'destacado'],
            'prompt_fragment': """
Enfócate en:
- Días/eventos con valores excepcionales
- Desviaciones del patrón normal
- Causas potenciales
- Implicaciones
"""
        },
        'geografico': {
            'nombre': 'Análisis Geográfico',
            'keywords': ['Montevideo', 'Mercedes', 'regional', 'localidad', 'territorial'],
            'prompt_fragment': """
Enfócate en:
- Performance comparada Montevideo vs Mercedes
- Tendencias por localidad
- Oportunidades geográficas
- Balance territorial
"""
        },
        'temporal': {
            'nombre': 'Análisis de Estacionalidad',
            'keywords': ['estacional', 'ciclo', 'patrón temporal', 'recurrente'],
            'prompt_fragment': """
Enfócate en:
- Patrones semanales/mensuales
- Estacionalidad detectada
- Ciclos de negocio
- Timing óptimo
"""
        },
        'comparativo': {
            'nombre': 'Benchmarking Interno',
            'keywords': ['comparar', 'mejor mes', 'récord', 'benchmark'],
            'prompt_fragment': """
Enfócate en:
- Comparación con mejor/peor mes histórico
- Distancia al objetivo
- Ranking de áreas
- Mejores prácticas internas
"""
        },
        'proyectivo': {
            'nombre': 'Proyecciones y Forecasting',
            'keywords': ['proyección', 'forecast', 'estimar', 'tendencia', 'fin de año'],
            'prompt_fragment': """
Enfócate en:
- Proyección fin de año basada en tendencia
- Escenarios optimista/pesimista
- Factores de riesgo
- Probabilidad de alcanzar metas
"""
        }
    }
    
    @classmethod
    def select_lenses(cls, period_type: str, month_number: int = None) -> List[str]:
        """
        Selecciona lentes apropiados para el período, rotando para evitar repetición.
        
        Args:
            period_type: 'weekly', 'monthly', 'quarterly', 'yearly'
            month_number: Número de mes (1-12) para rotación
            
        Returns:
            Lista de 3-4 nombres de lentes a aplicar
        """
        if period_type == 'monthly':
            # Rotar lentes según mes (evita mismo análisis mes tras mes)
            rotacion = [
                ['crecimiento', 'eficiencia', 'geografico'],      # Meses 1, 4, 7, 10
                ['concentracion', 'temporal', 'comparativo'],     # Meses 2, 5, 8, 11
                ['anomalias', 'proyectivo', 'geografico'],        # Meses 3, 6, 9, 12
            ]
            
            if month_number:
                idx = (month_number - 1) % 3
                return rotacion[idx]
            else:
                return ['crecimiento', 'eficiencia', 'comparativo']
        
        elif period_type == 'quarterly':
            return ['crecimiento', 'eficiencia', 'proyectivo', 'comparativo']
        
        elif period_type == 'yearly':
            return ['crecimiento', 'comparativo', 'proyectivo', 'geografico', 'temporal']
        
        else:
            # weekly
            return ['crecimiento', 'eficiencia']
    
    @classmethod
    def get_lens_config(cls, lens_name: str) -> Dict[str, Any]:
        """Retorna configuración de un lente específico"""
        return cls.LENSES.get(lens_name, cls.LENSES['crecimiento'])
    
    @classmethod
    def get_prompt_fragments(cls, lens_names: List[str]) -> str:
        """
        Construye fragmento de prompt combinando múltiples lentes.
        
        Args:
            lens_names: Lista de nombres de lentes a aplicar
            
        Returns:
            String con instrucciones combinadas para Claude
        """
        fragments = []
        
        for lens_name in lens_names:
            lens = cls.LENSES.get(lens_name)
            if lens:
                fragments.append(f"• {lens['nombre']}:")
                fragments.append(lens['prompt_fragment'])
        
        return "\n".join(fragments)

