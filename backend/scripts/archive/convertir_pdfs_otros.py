#!/usr/bin/env python3
"""
Script para convertir PDFs de carpeta "otros" a DOCX.

Convierte todos los PDFs de:
  /home/brunogandolfo/modelos_machado/otros/
  
A DOCX en:
  ~/modelos_machado_docx/otros/

Requiere: pip install pdf2docx
"""

import sys
from pathlib import Path
from typing import List, Tuple

try:
    from pdf2docx import Converter
except ImportError:
    print("ERROR: pdf2docx no está instalado.")
    print("Instalar con: pip install pdf2docx")
    sys.exit(1)


def convertir_pdf_a_docx(pdf_path: Path, docx_path: Path) -> Tuple[bool, str]:
    """
    Convierte un PDF a DOCX.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        cv = Converter(str(pdf_path))
        cv.convert(str(docx_path))
        cv.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)


def main():
    # Rutas
    carpeta_origen = Path("/home/brunogandolfo/modelos_machado/otros")
    carpeta_destino = Path.home() / "modelos_machado_docx" / "otros"
    
    # Crear carpeta destino si no existe
    carpeta_destino.mkdir(parents=True, exist_ok=True)
    
    # Obtener todos los PDFs
    pdfs = sorted(carpeta_origen.glob("*.pdf"))
    
    if not pdfs:
        print(f"❌ No se encontraron PDFs en: {carpeta_origen}")
        return
    
    print(f"📁 Encontrados {len(pdfs)} PDFs en: {carpeta_origen}")
    print(f"📁 Destino: {carpeta_destino}\n")
    
    # Estadísticas
    exitosos = 0
    fallidos = 0
    errores: List[Tuple[str, str]] = []
    
    # Procesar cada PDF
    for i, pdf_path in enumerate(pdfs, 1):
        nombre_base = pdf_path.stem
        docx_path = carpeta_destino / f"{nombre_base}.docx"
        
        # Verificar si ya existe
        if docx_path.exists():
            print(f"[{i}/{len(pdfs)}] ⏭️  Ya existe: {nombre_base}.docx")
            exitosos += 1
            continue
        
        print(f"[{i}/{len(pdfs)}] 🔄 Convirtiendo: {pdf_path.name}...", end=" ", flush=True)
        
        success, message = convertir_pdf_a_docx(pdf_path, docx_path)
        
        if success:
            print("✅")
            exitosos += 1
        else:
            print(f"❌ Error: {message}")
            fallidos += 1
            errores.append((pdf_path.name, message))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"✅ Exitosos: {exitosos}")
    print(f"❌ Fallidos: {fallidos}")
    print(f"📄 Total: {len(pdfs)}")
    
    if errores:
        print("\n❌ ERRORES:")
        for pdf_name, error in errores:
            print(f"  - {pdf_name}: {error}")
    
    print(f"\n📁 Archivos guardados en: {carpeta_destino}")


if __name__ == "__main__":
    main()
