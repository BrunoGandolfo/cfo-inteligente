#!/usr/bin/env python3
"""
Script para convertir PDFs a DOCX de carpetas: poderes, societario, sucesiones

Uso:
    cd /home/brunogandolfo/cfo-inteligente/backend
    source venv/bin/activate  # si usas venv
    python scripts/convertir_pdfs_docx.py
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Intentar importar pdf2docx, instalar si no está
try:
    from pdf2docx import Converter
except ImportError:
    print("📦 Instalando pdf2docx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdf2docx"])
    from pdf2docx import Converter

# Configuración
CARPETAS = ["poderes", "societario", "sucesiones"]
DIR_BASE_ENTRADA = Path.home() / "modelos_machado"
DIR_BASE_SALIDA = Path.home() / "modelos_machado_docx"


def convertir_pdf_a_docx(pdf_path: Path, docx_path: Path) -> bool:
    """
    Convierte un PDF a DOCX.
    
    Returns:
        True si la conversión fue exitosa, False en caso contrario
    """
    try:
        # Crear directorio de salida si no existe
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convertir
        cv = Converter(str(pdf_path))
        cv.convert(str(docx_path))
        cv.close()
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def procesar_carpeta(carpeta: str) -> Tuple[int, int]:
    """
    Procesa todos los PDFs de una carpeta.
    
    Returns:
        (exitosos, totales)
    """
    dir_entrada = DIR_BASE_ENTRADA / carpeta
    dir_salida = DIR_BASE_SALIDA / carpeta
    
    if not dir_entrada.exists():
        print(f"⚠️  Carpeta no encontrada: {dir_entrada}")
        return (0, 0)
    
    # Buscar todos los PDFs
    pdfs = list(dir_entrada.glob("*.pdf"))
    total = len(pdfs)
    
    if total == 0:
        print(f"📁 {carpeta}: No se encontraron PDFs")
        return (0, 0)
    
    print(f"\n📁 {carpeta}: {total} PDFs encontrados")
    print(f"   Entrada: {dir_entrada}")
    print(f"   Salida:  {dir_salida}")
    
    exitosos = 0
    
    for i, pdf_path in enumerate(pdfs, 1):
        nombre_base = pdf_path.stem
        docx_path = dir_salida / f"{nombre_base}.docx"
        
        # Verificar si ya existe
        if docx_path.exists():
            print(f"  [{i}/{total}] ⏭️  {nombre_base}.pdf (ya existe)")
            exitosos += 1
            continue
        
        print(f"  [{i}/{total}] 🔄 {nombre_base}.pdf...", end=" ", flush=True)
        
        if convertir_pdf_a_docx(pdf_path, docx_path):
            print("✅")
            exitosos += 1
        else:
            print("❌")
    
    return (exitosos, total)


def main():
    """Función principal"""
    print("=" * 80)
    print("CONVERSIÓN DE PDFs A DOCX".center(80))
    print("=" * 80)
    print(f"\n📂 Carpeta base entrada:  {DIR_BASE_ENTRADA}")
    print(f"📂 Carpeta base salida:   {DIR_BASE_SALIDA}")
    print(f"\n📋 Carpetas a procesar: {', '.join(CARPETAS)}")
    print("=" * 80)
    
    total_exitosos = 0
    total_archivos = 0
    
    for carpeta in CARPETAS:
        exitosos, totales = procesar_carpeta(carpeta)
        total_exitosos += exitosos
        total_archivos += totales
    
    print("\n" + "=" * 80)
    print("RESUMEN".center(80))
    print("=" * 80)
    print(f"✅ Exitosos: {total_exitosos}/{total_archivos}")
    print(f"❌ Fallidos: {total_archivos - total_exitosos}/{total_archivos}")
    print("=" * 80)
    
    if total_exitosos == total_archivos:
        print("\n🎉 ¡Conversión completada exitosamente!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_archivos - total_exitosos} archivos fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
