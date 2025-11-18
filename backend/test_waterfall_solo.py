from app.services.charts.chart_factory import ChartFactory
from PIL import Image

data = {
    'labels': ['Ingresos', 'Gastos', 'Retiros', 'Distribuciones', 'Resultado'],
    'values': [27564510, -3086702, -3400000, -8440469, 12637339],
    'measures': ['relative', 'relative', 'relative', 'relative', 'total']
}

path = ChartFactory.create_and_save(
    'waterfall',
    data,
    '/tmp/test_waterfall.png',
    {'title': 'Test Waterfall'}
)

print(f"✓ PNG generado: {path}")

# Verificar dimensiones REALES
img = Image.open(path)
print(f"📐 Dimensiones: {img.size}")
print(f"🎯 Esperado: ~4200x2775 (si scale=3)")
print(f"⚠️  Si es 2800x1850 → scale=3 NO se está aplicando")
