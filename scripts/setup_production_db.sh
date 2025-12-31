#!/bin/bash
# ===========================================
# CFO INTELIGENTE - Setup Base de Datos Producción
# ===========================================
# Ejecutar UNA sola vez para preparar la BD de producción
# Uso: ./scripts/setup_production_db.sh

set -e  # Salir si hay error

echo "=========================================="
echo "CFO INTELIGENTE - Setup Producción"
echo "=========================================="

# Verificar que PostgreSQL está corriendo
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql no está instalado"
    exit 1
fi

# Variables
DB_NAME="cfo_inteligente_prod"
DB_USER="cfo_user"

echo ""
echo "📦 Paso 1: Crear base de datos $DB_NAME"
echo "-------------------------------------------"

# Crear base de datos si no existe
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "✅ Base de datos $DB_NAME lista"

echo ""
echo "🔧 Paso 2: Ejecutar migraciones"
echo "-------------------------------------------"

# Cambiar a directorio backend
cd "$(dirname "$0")/../backend"

# Exportar DATABASE_URL para producción
export DATABASE_URL="postgresql://$DB_USER:cfo_pass@localhost:5432/$DB_NAME"

# Ejecutar migraciones
source venv/bin/activate 2>/dev/null || true
alembic upgrade head

echo "✅ Migraciones ejecutadas"

echo ""
echo "🌱 Paso 3: Ejecutar seeds (áreas y socios)"
echo "-------------------------------------------"

python scripts/seed_data.py

echo "✅ Seeds ejecutados"

echo ""
echo "=========================================="
echo "✅ Setup de producción completado"
echo "=========================================="
echo ""
echo "Base de datos: $DB_NAME"
echo "Tablas creadas con migraciones"
echo "Datos iniciales: 5 áreas + 5 socios"
echo ""
echo "⚠️  IMPORTANTE: Actualizar .env con:"
echo "    POSTGRES_DB=$DB_NAME"
echo "=========================================="
