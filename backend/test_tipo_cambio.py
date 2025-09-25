import sys
sys.path.insert(0, '.')

# Probar el servicio ORIGINAL
from app.services.tipo_cambio_service import obtener_tipo_cambio_actual as original

# Probar el servicio NUEVO
from app.services.tipo_cambio_service_v2 import obtener_tipo_cambio_actual as nuevo

print("=== SERVICIO ORIGINAL ===")
resultado_original = original()
print(f"Compra: {resultado_original['compra']}")
print(f"Venta: {resultado_original['venta']}")
print(f"Promedio: {resultado_original['promedio']}")

print("\n=== SERVICIO NUEVO ===")
resultado_nuevo = nuevo()
print(f"Compra: {resultado_nuevo['compra']}")
print(f"Venta: {resultado_nuevo['venta']}")
print(f"Promedio: {resultado_nuevo['promedio']}")

print("\n=== COMPATIBILIDAD ===")
print(f"Mismas keys: {set(resultado_original.keys()) == set(resultado_nuevo.keys())}")
