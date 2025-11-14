#!/bin/bash
# Script de ejecución rápida de auditoría SQL
# Uso: ./ejecutar_auditoria.sh

echo "🔍 Iniciando auditoría de queries SQL..."
echo ""

cd "$(dirname "$0")"

# Activar virtual environment si existe
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Ejecutar validador automático
python validador_queries_automatico.py

echo ""
echo "📋 Reportes generados en: backend/output/"
echo "   • queries_sospechosas.json"
echo "   • queries_sospechosas.md"
echo ""
echo "🎯 Para validación interactiva ejecutar:"
echo "   python validar_interactivo.py"
echo ""

