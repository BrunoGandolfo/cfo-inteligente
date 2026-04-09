#!/usr/bin/env python3
"""
Script para corregir operaciones con tipo_cambio erróneo (1.00)
"""
from sqlalchemy import create_engine, text
from decimal import Decimal
import sys
import requests
sys.path.append('/home/brunogandolfo/cfo-inteligente/backend')
from app.core.config import settings

# IDs de las operaciones con error encontradas
IDS_ERRONEOS = [
    '3e473a99-e134-48d3-81a6-c1f61a18ab5a',
    'b43afc37-5913-4a4e-ac02-dc34962a619b'
]

def obtener_tipo_cambio():
    """Obtener tipo de cambio actual de la API"""
    try:
        response = requests.get("http://localhost:8000/api/tipo-cambio/venta")
        if response.status_code == 200:
            tc = Decimal(str(response.json()))
            print(f"✅ Tipo de cambio obtenido de API: {tc}")
            return tc
    except:
        pass
    
    # Fallback si la API no responde
    tc = Decimal('41.05')
    print(f"⚠️ Usando tipo de cambio fallback: {tc}")
    return tc

def main():
    engine = create_engine(settings.DATABASE_URL)
    TIPO_CAMBIO_CORRECTO = obtener_tipo_cambio()
    
    with engine.begin() as conn:  # Usar engine.begin() directamente
        # Primero mostrar el estado actual
        print("\n🔍 ESTADO ACTUAL de las operaciones con error:\n")
        
        for op_id in IDS_ERRONEOS:
            result = conn.execute(text("""
                SELECT id, fecha, tipo_operacion, moneda_original, 
                       monto_original, tipo_cambio, monto_uyu, monto_usd
                FROM operaciones 
                WHERE id = :id
            """), {"id": op_id}).fetchone()
            
            if result:
                print(f"ID: {str(result[0])[:8]}...")
                print(f"  Fecha: {result[1]}, Tipo: {result[2]}")
                print(f"  Moneda: {result[3]}, Monto Original: {result[4]}")
                print(f"  TC ACTUAL (MAL): {result[5]}")
                print(f"  Montos actuales: UYU={result[6]}, USD={result[7]}")
                
                # Calcular valores correctos
                if result[3] == 'UYU':
                    nuevo_uyu = result[4]
                    nuevo_usd = result[4] / TIPO_CAMBIO_CORRECTO
                else:  # USD
                    nuevo_usd = result[4]
                    nuevo_uyu = result[4] * TIPO_CAMBIO_CORRECTO
                    
                print(f"  📐 VALORES CORRECTOS: UYU={nuevo_uyu:.2f}, USD={nuevo_usd:.2f}")
                print()
        
        # Confirmar antes de actualizar
        respuesta = input("\n¿Deseas CORREGIR estas operaciones? (s/n): ")
        
        if respuesta.lower() == 's':
            try:
                for op_id in IDS_ERRONEOS:
                    # Obtener datos actuales
                    result = conn.execute(text("""
                        SELECT moneda_original, monto_original
                        FROM operaciones 
                        WHERE id = :id
                    """), {"id": op_id}).fetchone()
                    
                    if result:
                        moneda, monto = result
                        
                        # Calcular nuevos montos
                        if moneda == 'UYU':
                            nuevo_uyu = monto
                            nuevo_usd = monto / TIPO_CAMBIO_CORRECTO
                        else:  # USD
                            nuevo_usd = monto
                            nuevo_uyu = monto * TIPO_CAMBIO_CORRECTO
                        
                        # Actualizar
                        conn.execute(text("""
                            UPDATE operaciones 
                            SET tipo_cambio = :tc,
                                monto_uyu = :uyu,
                                monto_usd = :usd,
                                updated_at = NOW()
                            WHERE id = :id
                        """), {
                            "tc": TIPO_CAMBIO_CORRECTO,
                            "uyu": nuevo_uyu,
                            "usd": nuevo_usd,
                            "id": op_id
                        })
                        
                        print(f"✅ Corregida operación {op_id[:8]}...")
                
                print("\n🎉 CORRECCIÓN COMPLETADA")
                
                # Verificar resultado
                print("\n📊 VERIFICACIÓN FINAL:")
                for op_id in IDS_ERRONEOS:
                    result = conn.execute(text("""
                        SELECT tipo_cambio, monto_uyu, monto_usd
                        FROM operaciones 
                        WHERE id = :id
                    """), {"id": op_id}).fetchone()
                    print(f"ID {op_id[:8]}... → TC={result[0]}, UYU={result[1]}, USD={result[2]}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                raise  # Re-lanzar para rollback automático
        else:
            print("❌ Corrección cancelada")

if __name__ == "__main__":
    main()
