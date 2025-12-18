"""
Script de prueba para generar reporte P&L por Localidad
Ejecutar: python test_pnl_localidad.py
"""

import sys
sys.path.insert(0, '/home/brunogandolfo/cfo-inteligente/backend')

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar modelos necesarios primero para evitar problemas de registro
import app.models  # Esto registra todos los modelos

from app.core.config import settings
from app.services.report_data.generators.pnl_localidad_generator import PnLLocalidadGenerator
from app.services.pdf.weasyprint_generator import PDFGenerator


def main():
    # Crear conexión directa
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Generar datos para Noviembre 2025
        generator = PnLLocalidadGenerator(db)
        datos = generator.generate(
            fecha_inicio=date(2025, 11, 1),
            fecha_fin=date(2025, 11, 30),
            comparar_con_anterior=True
        )
        
        print("=== DATOS GENERADOS ===")
        print(f"Período: {datos['metadata']['periodo_label']}")
        print(f"\nMONTEVIDEO:")
        print(f"  Ingresos: ${datos['montevideo']['actual']['ingresos']:,.2f}")
        print(f"  Resultado: ${datos['montevideo']['actual']['resultado_neto']:,.2f}")
        print(f"  Rentabilidad: {datos['montevideo']['actual']['rentabilidad']}%")
        print(f"  Ratio Extracción: {datos['montevideo']['actual']['ratio_extraccion']}%")
        
        print(f"\nMERCEDES:")
        print(f"  Ingresos: ${datos['mercedes']['actual']['ingresos']:,.2f}")
        print(f"  Resultado: ${datos['mercedes']['actual']['resultado_neto']:,.2f}")
        print(f"  Rentabilidad: {datos['mercedes']['actual']['rentabilidad']}%")
        print(f"  Ratio Extracción: {datos['mercedes']['actual']['ratio_extraccion']}%")
        
        print(f"\nTOTAL:")
        print(f"  Ingresos: ${datos['total']['actual']['ingresos']:,.2f}")
        print(f"  Resultado: ${datos['total']['actual']['resultado_neto']:,.2f}")
        
        # Generar PDF
        pdf_gen = PDFGenerator()
        pdf_bytes = pdf_gen.generar_pdf_desde_template(
            'reports/pnl_localidad.html',
            datos,
            '/tmp/pnl_localidad_noviembre.pdf'
        )
        
        print(f"\n✅ PDF generado: /tmp/pnl_localidad_noviembre.pdf")
        print(f"   Tamaño: {len(pdf_bytes):,} bytes")
        
    finally:
        db.close()


if __name__ == '__main__':
    main()

