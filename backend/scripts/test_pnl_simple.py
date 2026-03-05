"""
Script de prueba para generar reporte P&L por Localidad
Incluye narrativas con Claude Sonnet 4.5
Ejecutar: python test_pnl_simple.py
"""

import sys
sys.path.insert(0, '/home/brunogandolfo/cfo-inteligente/backend')

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv('/home/brunogandolfo/cfo-inteligente/backend/.env')

from datetime import date
from sqlalchemy import create_engine, text
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.core.config import settings

# Configuración DB desde settings
DATABASE_URL = settings.database_url


def format_currency_short(value):
    """Formatea como $27.8M"""
    if value is None:
        return "Sin Datos"
    try:
        num = float(value)
        if abs(num) >= 1_000_000:
            return f"${num/1_000_000:.1f}M"
        elif abs(num) >= 1_000:
            return f"${num/1_000:.1f}K"
        return f"${num:.0f}"
    except (ValueError, TypeError):
        return "Sin Datos"


def format_percent(value):
    """Formatea como 88.9%"""
    if value is None:
        return "Sin Datos"
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "Sin Datos"


def get_metricas_localidad(conn, fecha_inicio, fecha_fin, localidad):
    """Obtiene métricas para una localidad usando SQL directo."""
    
    sql = text("""
        SELECT 
            COALESCE(SUM(CASE WHEN tipo_operacion = 'INGRESO' THEN monto_uyu ELSE 0 END), 0) as ingresos,
            COALESCE(SUM(CASE WHEN tipo_operacion = 'GASTO' THEN monto_uyu ELSE 0 END), 0) as gastos,
            COALESCE(SUM(CASE WHEN tipo_operacion = 'RETIRO' THEN monto_uyu ELSE 0 END), 0) as retiros,
            COALESCE(SUM(CASE WHEN tipo_operacion = 'DISTRIBUCION' THEN monto_uyu ELSE 0 END), 0) as distribuciones,
            COUNT(*) as cantidad
        FROM operaciones
        WHERE fecha >= :fecha_inicio
          AND fecha <= :fecha_fin
          AND localidad = :localidad
          AND deleted_at IS NULL
    """)
    
    result = conn.execute(sql, {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'localidad': localidad
    }).fetchone()
    
    ingresos = float(result[0])
    gastos = float(result[1])
    retiros = float(result[2])
    distribuciones = float(result[3])
    
    resultado_neto = ingresos - gastos
    rentabilidad = (resultado_neto / ingresos * 100) if ingresos > 0 else 0
    
    return {
        'ingresos': round(ingresos, 2),
        'gastos': round(gastos, 2),
        'resultado_neto': round(resultado_neto, 2),
        'rentabilidad': round(rentabilidad, 2),
        'retiros': round(retiros, 2),
        'distribuciones': round(distribuciones, 2),
    }


def generar_narrativas_claude(datos):
    """Genera narrativas usando Claude Sonnet 4.5"""
    try:
        from app.services.ai.claude_client import ClaudeClient
        import json
        import re
        
        mvd = datos['montevideo']['actual']
        mer = datos['mercedes']['actual']
        total = datos['total']['actual']
        var = datos['total'].get('variaciones', {})
        
        prompt = f"""Analiza el desempeño financiero comparativo de las dos oficinas de Conexión Consultora (firma legal-contable uruguaya).

PERÍODO: {datos['metadata']['periodo_label']}

MONTEVIDEO:
- Ingresos: ${mvd['ingresos']:,.0f} ({mvd['ingresos']/total['ingresos']*100:.1f}% del total)
- Gastos: ${mvd['gastos']:,.0f}
- Resultado Neto: ${mvd['resultado_neto']:,.0f}
- Rentabilidad: {mvd['rentabilidad']:.1f}%

MERCEDES:
- Ingresos: ${mer['ingresos']:,.0f} ({mer['ingresos']/total['ingresos']*100:.1f}% del total)
- Gastos: ${mer['gastos']:,.0f}
- Resultado Neto: ${mer['resultado_neto']:,.0f}
- Rentabilidad: {mer['rentabilidad']:.1f}%

TOTALES CONSOLIDADOS:
- Ingresos: ${total['ingresos']:,.0f}
- Resultado Neto: ${total['resultado_neto']:,.0f}
- Rentabilidad: {total['rentabilidad']:.1f}%

GENERA UN ANÁLISIS EN FORMATO JSON:

{{
  "resumen_ejecutivo": "Párrafo de 2-3 oraciones resumiendo el desempeño general. Menciona cifras clave.",
  "analisis_montevideo": "Párrafo analizando Montevideo. Máximo 80 palabras.",
  "analisis_mercedes": "Párrafo analizando Mercedes. Máximo 80 palabras.",
  "comparativa": "Párrafo comparando ambas oficinas. Máximo 80 palabras.",
  "fortaleza_1": "Primera fortaleza (1 oración)",
  "fortaleza_2": "Segunda fortaleza (1 oración)",
  "atencion_1": "Primer punto de atención (1 oración)",
  "atencion_2": "Segundo punto de atención (1 oración)",
  "recomendacion_1": "Primera recomendación estratégica",
  "recomendacion_2": "Segunda recomendación estratégica",
  "recomendacion_3": "Tercera recomendación estratégica"
}}

RESPONDE SOLO CON EL JSON."""

        system_prompt = """Eres un CFO senior con 20 años de experiencia en firmas de servicios profesionales.
Tu análisis debe ser CONCRETO, ACCIONABLE y PROFESIONAL.
Responde SIEMPRE en JSON válido sin texto adicional."""
        
        claude = ClaudeClient()
        response = claude.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=800,
            system_prompt=system_prompt
        )
        
        # Limpiar respuesta
        clean_response = re.sub(r'```json\s*|\s*```', '', response).strip()
        narrativas = json.loads(clean_response)
        
        return narrativas
        
    except Exception as e:
        print(f"⚠️ Error con Claude: {e}")
        print("   Usando narrativas de fallback...")
        return generar_narrativas_fallback(datos)


def generar_narrativas_fallback(datos):
    """Genera narrativas básicas sin IA"""
    mvd = datos['montevideo']['actual']
    mer = datos['mercedes']['actual']
    total = datos['total']['actual']
    
    lider = "Montevideo" if mvd['ingresos'] > mer['ingresos'] else "Mercedes"
    pct_lider = max(mvd['ingresos'], mer['ingresos']) / total['ingresos'] * 100 if total['ingresos'] > 0 else 0
    
    return {
        "resumen_ejecutivo": f"En {datos['metadata']['periodo_label']}, Conexión Consultora registró ingresos de ${total['ingresos']:,.0f} con una rentabilidad del {total['rentabilidad']:.1f}%. {lider} lideró la facturación con el {pct_lider:.1f}% del total.",
        "analisis_montevideo": f"Montevideo generó ${mvd['ingresos']:,.0f} con rentabilidad de {mvd['rentabilidad']:.1f}%.",
        "analisis_mercedes": f"Mercedes generó ${mer['ingresos']:,.0f} con rentabilidad de {mer['rentabilidad']:.1f}%.",
        "comparativa": f"{lider} concentra la mayor parte de los ingresos del período.",
        "fortaleza_1": f"Rentabilidad consolidada del {total['rentabilidad']:.1f}%.",
        "fortaleza_2": f"Resultado neto positivo de ${total['resultado_neto']:,.0f}.",
        "atencion_1": "Monitorear equilibrio entre localidades.",
        "atencion_2": "Revisar sostenibilidad de extracciones.",
        "recomendacion_1": "Analizar mix de servicios por localidad.",
        "recomendacion_2": "Establecer política de retención mínima.",
        "recomendacion_3": "Revisar asignación de gastos entre oficinas."
    }


def main():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        fecha_inicio = date(2025, 11, 1)
        fecha_fin = date(2025, 11, 30)
        
        # Obtener datos
        mvd = get_metricas_localidad(conn, fecha_inicio, fecha_fin, 'MONTEVIDEO')
        mer = get_metricas_localidad(conn, fecha_inicio, fecha_fin, 'MERCEDES')
        
        # Calcular totales
        total = {
            'ingresos': mvd['ingresos'] + mer['ingresos'],
            'gastos': mvd['gastos'] + mer['gastos'],
            'resultado_neto': mvd['resultado_neto'] + mer['resultado_neto'],
            'retiros': mvd['retiros'] + mer['retiros'],
            'distribuciones': mvd['distribuciones'] + mer['distribuciones'],
        }
        total['rentabilidad'] = (total['resultado_neto'] / total['ingresos'] * 100) if total['ingresos'] > 0 else 0
        
        print("=== DATOS GENERADOS (Noviembre 2025) ===")
        print(f"\nMONTEVIDEO:")
        print(f"  Ingresos: ${mvd['ingresos']:,.2f}")
        print(f"  Resultado: ${mvd['resultado_neto']:,.2f}")
        print(f"  Rentabilidad: {mvd['rentabilidad']:.1f}%")
        
        print(f"\nMERCEDES:")
        print(f"  Ingresos: ${mer['ingresos']:,.2f}")
        print(f"  Resultado: ${mer['resultado_neto']:,.2f}")
        print(f"  Rentabilidad: {mer['rentabilidad']:.1f}%")
        
        print(f"\nTOTAL:")
        print(f"  Ingresos: ${total['ingresos']:,.2f}")
        print(f"  Resultado: ${total['resultado_neto']:,.2f}")
        print(f"  Rentabilidad: {total['rentabilidad']:.1f}%")
        
        # Preparar datos para template
        datos = {
            'metadata': {
                'periodo_label': 'Noviembre 2025',
                'fecha_generacion': date.today().isoformat(),
            },
            'montevideo': {'actual': mvd, 'variaciones': {}},
            'mercedes': {'actual': mer, 'variaciones': {}},
            'total': {'actual': total, 'variaciones': {}},
            'comparativa': [
                {'metrica': 'Ingresos', 'montevideo': mvd['ingresos'], 'montevideo_pct': round(mvd['ingresos']/total['ingresos']*100, 1) if total['ingresos'] > 0 else 0, 'mercedes': mer['ingresos'], 'mercedes_pct': round(mer['ingresos']/total['ingresos']*100, 1) if total['ingresos'] > 0 else 0, 'total': total['ingresos']},
                {'metrica': 'Gastos', 'montevideo': mvd['gastos'], 'montevideo_pct': round(mvd['gastos']/total['gastos']*100, 1) if total['gastos'] > 0 else 0, 'mercedes': mer['gastos'], 'mercedes_pct': round(mer['gastos']/total['gastos']*100, 1) if total['gastos'] > 0 else 0, 'total': total['gastos']},
                {'metrica': 'Resultado Neto', 'montevideo': mvd['resultado_neto'], 'montevideo_pct': round(mvd['resultado_neto']/total['resultado_neto']*100, 1) if total['resultado_neto'] > 0 else 0, 'mercedes': mer['resultado_neto'], 'mercedes_pct': round(mer['resultado_neto']/total['resultado_neto']*100, 1) if total['resultado_neto'] > 0 else 0, 'total': total['resultado_neto']},
            ],
        }
        
        # Generar narrativas con Claude
        print("\n=== GENERANDO NARRATIVAS CON CLAUDE ===")
        narrativas = generar_narrativas_claude(datos)
        datos['narrativas'] = narrativas
        
        print(f"\n=== NARRATIVAS CLAUDE ===")
        if narrativas:
            print(f"Resumen: {narrativas.get('resumen_ejecutivo', 'N/A')[:100]}...")
            print(f"Fortaleza 1: {narrativas.get('fortaleza_1', 'N/A')}")
            print(f"Recomendación 1: {narrativas.get('recomendacion_1', 'N/A')}")
        else:
            print("No se generaron narrativas")
        
        # Renderizar template
        templates_dir = Path('/home/brunogandolfo/cfo-inteligente/backend/app/templates/reports_big4')
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        env.filters['format_currency_short'] = format_currency_short
        env.filters['format_percent'] = format_percent
        env.filters['abs'] = abs
        env.filters['round'] = round
        
        template = env.get_template('reports/pnl_localidad.html')
        html_content = template.render(**datos)
        
        # Guardar HTML
        html_path = '/tmp/pnl_localidad_noviembre.html'
        with open(html_path, 'w') as f:
            f.write(html_content)
        print(f"\n✅ HTML generado: {html_path}")
        
        # Generar PDF con WeasyPrint
        try:
            from weasyprint import HTML
            pdf_path = '/tmp/pnl_localidad_noviembre.pdf'
            HTML(string=html_content).write_pdf(pdf_path)
            print(f"✅ PDF generado: {pdf_path}")
            
            import os
            size = os.path.getsize(pdf_path)
            print(f"   Tamaño: {size:,} bytes")
            print(f"\n📄 Reporte de 4 páginas con narrativas de Claude generado exitosamente!")
        except Exception as e:
            print(f"⚠️ Error generando PDF: {e}")
            print("   El HTML fue generado correctamente, revísalo en el navegador.")


if __name__ == '__main__':
    main()
