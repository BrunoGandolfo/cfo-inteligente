#!/bin/bash
set -e

echo "Ejecutando migraciones..."
echo "Migraciones desactivadas - BD restaurada desde dump"

echo "Iniciando servidor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
