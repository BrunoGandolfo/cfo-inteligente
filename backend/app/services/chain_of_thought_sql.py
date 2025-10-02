"""
Chain-of-Thought SQL Generation - Sistema CFO Inteligente

Genera SQL en 2 pasos para queries temporales complejas:
1. Obtener metadatos (fecha actual, meses con datos, meses restantes)
2. Generar SQL final usando metadatos REALES (no asumidos)

Resuelve problemas de:
- Proyecciones hardcodeadas
- "Últimos X meses" mal calculados
- Asunciones incorrectas sobre período de datos

Autor: Sistema CFO Inteligente
Versión: 1.0
Fecha: Octubre 2025
"""

from typing import Dict, Any, Optional, List
import anthropic
import os


class ChainOfThoughtSQL:
    """
    Generador SQL en 2 pasos con Chain-of-Thought
    """
    
    # Keywords que indican necesidad de metadatos temporales
    KEYWORDS_TEMPORALES = [
        'proyección', 'proyeccion', 'proyectar',
        'últimos', 'ultimos', 'últimas', 'ultimas',
        'tendencia', 'evolución', 'evolucion',
        'promedio', 'media',
        'basado en', 'en base a',
        'fin de año', 'fin del año', 'cierre',
        'comparar', 'vs anterior', 'versus',
        'crecimiento', 'variación', 'variacion',
        'estimar', 'estimación', 'estimacion'
    ]
    
    @classmethod
    def necesita_metadatos(cls, pregunta: str) -> bool:
        """
        Detecta si la pregunta requiere metadatos temporales
        
        Args:
            pregunta: Pregunta del usuario
            
        Returns:
            True si necesita Chain-of-Thought, False para flujo normal
        """
        pregunta_lower = pregunta.lower()
        return any(keyword in pregunta_lower for keyword in cls.KEYWORDS_TEMPORALES)
    
    @staticmethod
    def generar_sql_metadatos() -> str:
        """
        Genera SQL para obtener metadatos temporales del sistema
        
        Returns:
            SQL que devuelve: fecha_actual, año_actual, mes_actual,
            meses_con_datos_2025, meses_restantes_2025, ultimo_mes_con_datos
        """
        return """
SELECT 
    CURRENT_DATE as fecha_actual,
    EXTRACT(YEAR FROM CURRENT_DATE)::int as año_actual,
    EXTRACT(MONTH FROM CURRENT_DATE)::int as mes_actual,
    (SELECT COUNT(DISTINCT DATE_TRUNC('month', fecha))
     FROM operaciones
     WHERE deleted_at IS NULL
       AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)) as meses_con_datos_2025,
    12 - EXTRACT(MONTH FROM CURRENT_DATE)::int as meses_restantes_2025,
    (SELECT MAX(DATE_TRUNC('month', fecha))
     FROM operaciones
     WHERE deleted_at IS NULL) as ultimo_mes_con_datos,
    (SELECT MIN(DATE_TRUNC('month', fecha))
     FROM operaciones
     WHERE deleted_at IS NULL
       AND DATE_TRUNC('year', fecha) = DATE_TRUNC('year', CURRENT_DATE)) as primer_mes_con_datos_2025
"""
    
    @staticmethod
    def formatear_metadatos_para_prompt(metadatos: Dict[str, Any]) -> str:
        """
        Formatea metadatos en texto legible para Claude
        
        Args:
            metadatos: Dict con fecha_actual, mes_actual, meses_con_datos, etc.
            
        Returns:
            String formateado para incluir en prompt
        """
        fecha_actual = metadatos.get('fecha_actual', 'N/A')
        mes_actual = metadatos.get('mes_actual', 0)
        meses_con_datos = metadatos.get('meses_con_datos_2025', 0)
        meses_restantes = metadatos.get('meses_restantes_2025', 0)
        ultimo_mes = metadatos.get('ultimo_mes_con_datos', 'N/A')
        
        return f"""
═══════════════════════════════════════════════════════════════
METADATOS TEMPORALES DEL SISTEMA (NO RECALCULAR):
═══════════════════════════════════════════════════════════════
• Fecha actual (hoy): {fecha_actual}
• Mes actual: {mes_actual} (de 12)
• Meses con datos en 2025: {meses_con_datos}
• Meses restantes en 2025: {meses_restantes}
• Último mes con datos: {ultimo_mes}

IMPORTANTE: NO calcules estos valores de nuevo, YA están calculados arriba.
Para proyecciones usa: meses_restantes = {meses_restantes}
Para "últimos X meses" usa los datos desde {ultimo_mes} hacia atrás.
═══════════════════════════════════════════════════════════════
"""
    
    @staticmethod
    def generar_sql_con_contexto(
        pregunta: str,
        metadatos_str: str,
        claude_gen  # ClaudeSQLGenerator instance
    ) -> str:
        """
        Genera SQL usando Claude CON contexto temporal real
        
        Args:
            pregunta: Pregunta del usuario
            metadatos_str: Metadatos formateados
            claude_gen: Instancia de ClaudeSQLGenerator
            
        Returns:
            SQL generado con conocimiento de fecha actual y meses con datos
        """
        # Construir prompt enriquecido
        prompt_enriquecido = f"""{claude_gen.DDL_CONTEXT}

{claude_gen.BUSINESS_CONTEXT}

{metadatos_str}

PREGUNTA DEL USUARIO: {pregunta}

INSTRUCCIONES:
• Genera SOLO el SQL query en PostgreSQL, sin explicaciones ni markdown
• NO uses triple backticks ni formato ```sql
• El SQL debe ser ejecutable directamente
• USA los metadatos temporales de arriba (NO los recalcules)
• Si la pregunta pide proyección, usa meses_restantes del contexto
• Si pide "últimos X meses", calcula desde el último_mes_con_datos
• SIEMPRE incluye WHERE deleted_at IS NULL

Genera ÚNICAMENTE el SQL query:"""
        
        try:
            response = claude_gen.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt_enriquecido}]
            )
            
            sql_generado = response.content[0].text.strip()
            
            # Limpiar si viene con markdown
            if sql_generado.startswith("```"):
                sql_generado = sql_generado.replace("```sql", "").replace("```", "").strip()
            
            # DEBUG: Mostrar SQL generado con contexto
            print(f"   [CoT DEBUG] SQL GENERADO CON CONTEXTO:")
            print(f"{sql_generado}")
            print(f"   [CoT DEBUG] ─────────────────────────────")
            
            return sql_generado
            
        except Exception as e:
            print(f"Error en Chain-of-Thought SQL: {e}")
            return f"ERROR: {str(e)}"


# ══════════════════════════════════════════════════════════════
# FUNCIÓN DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════

def generar_con_chain_of_thought(
    pregunta: str,
    db_session,
    claude_generator
) -> Dict[str, Any]:
    """
    Wrapper que ejecuta Chain-of-Thought completo
    
    Args:
        pregunta: Pregunta del usuario
        db_session: Sesión de SQLAlchemy
        claude_generator: Instancia de ClaudeSQLGenerator
        
    Returns:
        {
            'sql': str,
            'metadatos_usados': dict,
            'metodo': 'chain_of_thought',
            'pasos': 2
        }
    """
    from sqlalchemy import text
    
    print("🔗 [Chain-of-Thought] Detectada pregunta temporal compleja")
    
    # PASO 1: Obtener metadatos
    sql_metadatos = ChainOfThoughtSQL.generar_sql_metadatos()
    
    print(f"📊 [Chain-of-Thought] Obteniendo metadatos temporales...")
    
    try:
        result = db_session.execute(text(sql_metadatos))
        row = result.fetchone()
        
        if not row:
            raise ValueError("No se pudieron obtener metadatos")
        
        metadatos = dict(row._mapping)
        
        print(f"   ✅ Metadatos obtenidos:")
        print(f"      - Fecha actual: {metadatos.get('fecha_actual')}")
        print(f"      - Meses con datos 2025: {metadatos.get('meses_con_datos_2025')}")
        print(f"      - Meses restantes: {metadatos.get('meses_restantes_2025')}")
        
        # PASO 2: Generar SQL final con contexto
        metadatos_str = ChainOfThoughtSQL.formatear_metadatos_para_prompt(metadatos)
        
        print(f"🎯 [Chain-of-Thought] Generando SQL final con contexto temporal...")
        
        sql_final = ChainOfThoughtSQL.generar_sql_con_contexto(
            pregunta,
            metadatos_str,
            claude_generator
        )
        
        print(f"   ✅ SQL generado con Chain-of-Thought")
        
        return {
            'sql': sql_final,
            'metadatos_usados': metadatos,
            'metodo': 'chain_of_thought',
            'pasos': 2,
            'exito': True
        }
    
    except Exception as e:
        print(f"   ❌ Error en Chain-of-Thought: {e}")
        return {
            'sql': None,
            'metadatos_usados': {},
            'metodo': 'chain_of_thought_failed',
            'pasos': 2,
            'exito': False,
            'error': str(e)
        }


# ══════════════════════════════════════════════════════════════
# TESTING
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*80)
    print("🧪 TESTING CHAIN-OF-THOUGHT SQL")
    print("="*80)
    
    # Test de detección
    preguntas_test = [
        ("¿Cuánto facturamos este mes?", False),  # Simple, no necesita CoT
        ("Proyección de fin de año", True),  # Necesita metadatos
        ("Tendencia últimos 6 meses", True),  # Necesita metadatos
        ("¿Qué área es más rentable?", False),  # Simple
        ("Evolución basada en últimos 8 meses", True),  # Necesita metadatos
    ]
    
    for pregunta, esperado in preguntas_test:
        necesita = ChainOfThoughtSQL.necesita_metadatos(pregunta)
        simbolo = "✅" if necesita == esperado else "❌"
        print(f"{simbolo} '{pregunta[:40]}...' → Necesita CoT: {necesita} (esperado: {esperado})")
    
    # Test SQL de metadatos
    print(f"\n{'='*80}")
    print("SQL DE METADATOS:")
    print("="*80)
    sql_meta = ChainOfThoughtSQL.generar_sql_metadatos()
    print(sql_meta)

