"""
InsightFormatter - Formatea insights para presentación

Convierte JSON de insights a HTML/texto formateado para PDF.
Aplica estilos según tipo de insight.

Autor: Sistema CFO Inteligente
Fecha: Octubre 2025
"""

from typing import List, Dict, Any


class InsightFormatter:
    """
    Formatea insights para diferentes formatos de salida.
    """
    
    # Íconos/estilos por tipo de insight
    STYLES = {
        'tendencia': {
            'icon': '📈',
            'color': '#3B82F6',  # Azul
            'bg': '#EBF5FF'
        },
        'alerta': {
            'icon': '⚠️',
            'color': '#F59E0B',  # Ámbar
            'bg': '#FFF7ED'
        },
        'destacado': {
            'icon': '⭐',
            'color': '#10B981',  # Verde
            'bg': '#ECFDF5'
        },
        'oportunidad': {
            'icon': '💡',
            'color': '#8B5CF6',  # Violeta
            'bg': '#F5F3FF'
        }
    }
    
    @classmethod
    def format_to_html(cls, insights: List[Dict[str, str]]) -> str:
        """
        Convierte lista de insights a HTML con estilos.
        
        Args:
            insights: Lista de insights estructurados
            
        Returns:
            String HTML listo para embeber en template
        """
        html_parts = []
        
        for insight in insights:
            tipo = insight.get('tipo', 'destacado')
            style = cls.STYLES.get(tipo, cls.STYLES['destacado'])
            
            html = f"""
<div class="insight-box {tipo}" style="background-color: {style['bg']}; border-left: 4px solid {style['color']}; padding: 1rem; margin-bottom: 1rem;">
    <div class="insight-header" style="display: flex; align-items: center; margin-bottom: 0.5rem;">
        <span class="icon" style="font-size: 1.5rem; margin-right: 0.5rem;">{style['icon']}</span>
        <h4 style="margin: 0; color: {style['color']}; font-size: 1.1rem;">{insight['titulo']}</h4>
    </div>
    <p class="insight-description" style="margin: 0; color: #374151; line-height: 1.6;">
        {insight['descripcion']}
    </p>
</div>
"""
            html_parts.append(html)
        
        return "\n".join(html_parts)
    
    @classmethod
    def format_to_markdown(cls, insights: List[Dict[str, str]]) -> str:
        """Formato Markdown (útil para debugging o emails)"""
        md_parts = []
        
        for insight in insights:
            tipo = insight.get('tipo', 'destacado')
            style = cls.STYLES.get(tipo, cls.STYLES['destacado'])
            
            md = f"""
{style['icon']} **{insight['titulo']}**

{insight['descripcion']}

---
"""
            md_parts.append(md)
        
        return "\n".join(md_parts)

