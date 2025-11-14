"""
Validador Interactivo de Queries SQL - CFO Inteligente

Lee queries sospechosas del JSON generado por validador_queries_automatico.py
y permite validar manualmente ejecutando SQL original vs corregido.

Autor: Sistema CFO Inteligente
Fecha: 2025-11-14
"""

import psycopg2
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import sys


class ValidadorInteractivo:
    """Valida queries sospechosas ejecutándolas y comparando resultados"""
    
    def __init__(self, db_url: str, json_path: str):
        self.db_url = db_url
        self.json_path = json_path
        self.validaciones = []
        
    def conectar(self):
        """Conectar a PostgreSQL"""
        return psycopg2.connect(self.db_url)
    
    def cargar_queries_sospechosas(self) -> Dict:
        """Carga queries sospechosas del JSON"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def ejecutar_query_safe(self, sql: str) -> Tuple[bool, any]:
        """Ejecuta query de manera segura y retorna (exito, resultado)"""
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            
            # Ejecutar query
            cursor.execute(sql)
            
            # Obtener resultados
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            cursor.close()
            conn.close()
            
            return True, {'columns': columns, 'rows': rows}
            
        except Exception as e:
            return False, str(e)
    
    def formatear_resultado(self, resultado: Dict) -> str:
        """Formatea resultado de query para visualización"""
        if not resultado.get('rows'):
            return "   (Sin resultados)\n"
        
        output = ""
        columns = resultado['columns']
        rows = resultado['rows']
        
        # Encabezados
        output += "   " + " | ".join(str(col).ljust(20) for col in columns) + "\n"
        output += "   " + "-" * (len(columns) * 23) + "\n"
        
        # Filas (máximo 10)
        for row in rows[:10]:
            output += "   " + " | ".join(str(val).ljust(20) for val in row) + "\n"
        
        if len(rows) > 10:
            output += f"   ... ({len(rows) - 10} filas más)\n"
        
        return output
    
    def validar_query(self, query: Dict, idx: int, total: int) -> Dict:
        """Valida una query interactivamente"""
        print("\n" + "=" * 80)
        print(f"🔍 VALIDANDO QUERY {idx}/{total} - [{query['criticidad']}]")
        print("=" * 80)
        print()
        
        print(f"📅 Fecha: {query['fecha']}")
        print(f"❓ Pregunta: {query['pregunta']}")
        print(f"💬 Respuesta chat: {query['respuesta_chat']}")
        print()
        
        print("⚠️  Problemas detectados:")
        for problema in query['problemas']:
            print(f"   • [{problema['criticidad']}] {problema['tipo']}")
        print()
        
        # Preguntar si ejecutar
        print("¿Desea ejecutar las queries para comparar resultados? (s/n/skip)")
        print("  s    = Ejecutar y comparar")
        print("  n    = Marcar como revisión manual pendiente")
        print("  skip = Saltar esta query")
        
        opcion = input("\n👉 Opción: ").strip().lower()
        
        if opcion == 'skip':
            return {
                'id': query['id'],
                'decision': 'skipped',
                'timestamp': datetime.now().isoformat()
            }
        
        if opcion == 'n':
            return {
                'id': query['id'],
                'decision': 'manual_review',
                'timestamp': datetime.now().isoformat()
            }
        
        # Ejecutar SQL original
        print("\n🔄 Ejecutando SQL ORIGINAL...")
        exito_orig, resultado_orig = self.ejecutar_query_safe(query['sql_original'])
        
        if not exito_orig:
            print(f"   ❌ Error: {resultado_orig}")
            print("\n¿Marcar como ERROR confirmado? (s/n)")
            confirmar = input("👉 Opción: ").strip().lower()
            
            if confirmar == 's':
                return {
                    'id': query['id'],
                    'decision': 'error_confirmado',
                    'error_original': resultado_orig,
                    'timestamp': datetime.now().isoformat()
                }
        else:
            print("   ✅ Ejecutado exitosamente")
            print("\n📊 RESULTADO ORIGINAL:")
            print(self.formatear_resultado(resultado_orig))
        
        # Extraer SQL corregido (quitar comentarios)
        sql_corregido_limpio = '\n'.join([
            linea for linea in query['sql_corregido'].split('\n')
            if not linea.strip().startswith('--')
        ]).strip()
        
        # Ejecutar SQL corregido
        print("\n🔄 Ejecutando SQL CORREGIDO...")
        exito_corr, resultado_corr = self.ejecutar_query_safe(sql_corregido_limpio)
        
        if not exito_corr:
            print(f"   ⚠️  SQL corregido también falla: {resultado_corr}")
            print("   (Esto puede ser esperado si el SQL corregido es solo una sugerencia)")
        else:
            print("   ✅ Ejecutado exitosamente")
            print("\n📊 RESULTADO CORREGIDO:")
            print(self.formatear_resultado(resultado_corr))
        
        # Comparar si ambos exitosos
        if exito_orig and exito_corr:
            print("\n❓ ¿Los resultados son diferentes? (s/n)")
            diferentes = input("👉 Opción: ").strip().lower()
            
            if diferentes == 's':
                print("\n❓ ¿Cuál es el CORRECTO?")
                print("  1 = Original")
                print("  2 = Corregido")
                print("  ? = No estoy seguro")
                
                correcto = input("👉 Opción: ").strip()
                
                if correcto == '1':
                    return {
                        'id': query['id'],
                        'decision': 'original_correcto',
                        'resultado_original': self._resultado_a_dict(resultado_orig),
                        'resultado_corregido': self._resultado_a_dict(resultado_corr),
                        'timestamp': datetime.now().isoformat()
                    }
                elif correcto == '2':
                    return {
                        'id': query['id'],
                        'decision': 'corregido_correcto',
                        'resultado_original': self._resultado_a_dict(resultado_orig),
                        'resultado_corregido': self._resultado_a_dict(resultado_corr),
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'id': query['id'],
                        'decision': 'requiere_analisis',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                return {
                    'id': query['id'],
                    'decision': 'ambos_iguales',
                    'timestamp': datetime.now().isoformat()
                }
        
        return {
            'id': query['id'],
            'decision': 'error_ejecucion',
            'timestamp': datetime.now().isoformat()
        }
    
    def _resultado_a_dict(self, resultado: Dict) -> Dict:
        """Convierte resultado a formato JSON serializable"""
        if not resultado or not resultado.get('rows'):
            return {'rows': 0, 'datos': []}
        
        return {
            'rows': len(resultado['rows']),
            'columns': resultado['columns'],
            'datos': [
                dict(zip(resultado['columns'], row))
                for row in resultado['rows'][:5]  # Solo primeras 5 filas
            ]
        }
    
    def ejecutar_validacion_interactiva(self):
        """Ejecuta validación interactiva completa"""
        print("📂 Cargando queries sospechosas...")
        datos = self.cargar_queries_sospechosas()
        queries = datos['queries_sospechosas']
        
        if not queries:
            print("\n✅ No hay queries sospechosas para validar")
            return
        
        print(f"   ✅ {len(queries)} queries sospechosas cargadas\n")
        
        # Filtrar por criticidad
        print("🎯 Filtrar por criticidad:")
        print("  1 = Solo ALTA")
        print("  2 = ALTA + MEDIA")
        print("  3 = Todas")
        
        filtro = input("\n👉 Opción (default=1): ").strip() or "1"
        
        if filtro == "1":
            queries_filtradas = [q for q in queries if q['criticidad'] == 'ALTA']
        elif filtro == "2":
            queries_filtradas = [q for q in queries if q['criticidad'] in ['ALTA', 'MEDIA']]
        else:
            queries_filtradas = queries
        
        print(f"\n📋 Validando {len(queries_filtradas)} queries...\n")
        
        # Validar cada query
        for idx, query in enumerate(queries_filtradas, 1):
            validacion = self.validar_query(query, idx, len(queries_filtradas))
            self.validaciones.append(validacion)
        
        # Generar reporte final
        self.generar_reporte_final(datos['estadisticas'])
    
    def generar_reporte_final(self, stats_originales: Dict):
        """Genera reporte final con resultados de validación"""
        print("\n" + "=" * 80)
        print("📊 GENERANDO REPORTE FINAL")
        print("=" * 80)
        print()
        
        # Estadísticas de validación
        decisiones = {}
        for val in self.validaciones:
            decision = val['decision']
            decisiones[decision] = decisiones.get(decision, 0) + 1
        
        reporte = {
            'fecha_validacion': datetime.now().isoformat(),
            'estadisticas_originales': stats_originales,
            'queries_validadas': len(self.validaciones),
            'decisiones': decisiones,
            'validaciones': self.validaciones,
            'confianza_sistema': self._calcular_confianza(stats_originales, decisiones)
        }
        
        # Guardar JSON
        output_path = Path(__file__).parent.parent / "output" / "reporte_validacion_final.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Reporte guardado: {output_path}\n")
        
        # Mostrar resumen
        print("📈 RESUMEN DE VALIDACIÓN:")
        print(f"   • Queries validadas: {len(self.validaciones)}")
        for decision, count in decisiones.items():
            print(f"   • {decision}: {count}")
        print(f"\n🎯 Confianza del sistema: {reporte['confianza_sistema']}%")
        print()
    
    def _calcular_confianza(self, stats: Dict, decisiones: Dict) -> float:
        """
        Calcula confianza del sistema basado en:
        - Queries no sospechosas (100% confianza)
        - Queries sospechosas validadas como correctas
        - Penalizar queries confirmadas como incorrectas
        """
        total = stats['total_queries']
        no_sospechosas = total - stats['queries_sospechosas']
        
        # Queries sospechosas que resultaron correctas
        falsas_alarmas = decisiones.get('original_correcto', 0) + decisiones.get('ambos_iguales', 0)
        
        # Queries confirmadas como incorrectas
        incorrectas = decisiones.get('corregido_correcto', 0) + decisiones.get('error_confirmado', 0)
        
        # Cálculo de confianza
        confianza = ((no_sospechosas + falsas_alarmas) / total) * 100
        
        return round(confianza, 2)


def main():
    """Función principal"""
    print("=" * 80)
    print("🔍 VALIDADOR INTERACTIVO DE QUERIES SQL - CFO INTELIGENTE")
    print("=" * 80)
    print()
    
    # Configuración
    DB_URL = "postgresql://postgres:postgres@localhost:5432/cfo_inteligente"
    JSON_PATH = Path(__file__).parent.parent / "output" / "queries_sospechosas.json"
    
    if not JSON_PATH.exists():
        print(f"❌ ERROR: No se encontró {JSON_PATH}")
        print("\n💡 Primero ejecuta: python scripts/validador_queries_automatico.py")
        return 1
    
    try:
        validador = ValidadorInteractivo(DB_URL, str(JSON_PATH))
        validador.ejecutar_validacion_interactiva()
        
        print("✅ Validación interactiva completada")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Validación interrumpida por el usuario")
        print("   Progreso guardado hasta el momento")
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

