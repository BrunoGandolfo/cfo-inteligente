#!/bin/bash
# Script de instalación de Playwright y Chromium
# Para sistema de reportes PDF CFO Inteligente

echo "🚀 Instalando Playwright..."
pip install playwright==1.48.0

echo "📦 Instalando navegador Chromium..."
playwright install chromium

echo "✅ Instalación completada"
echo ""
echo "Playwright está listo para generar PDFs profesionales."

