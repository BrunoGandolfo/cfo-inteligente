"""
Validador Automático de Queries SQL - CFO Inteligente

Detecta patrones problemáticos en queries generadas por Claude
y genera reportes de queries sospechosas con SQL corregido.

Autor: Sistema CFO Inteligente
Fecha: 2025-11-14
"""

import psycopg2
import json
import re
from datetime import datetime
from typing import List, Dict, Tuple
import os
from pathlib import Path


class ValidadorQuerysAutomatico:
    """Detecta patrones problemáticos en queries SQL generadas"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.queries_analizadas = []
        self.queries_sospechosas = []
        
    def conectar(self):
        """Conectar a PostgreSQL"""
        return psycopg2.connect(self.db_url)
    
    def extraer_queries(self) -> List[Dict]:
        """Extrae todas las queries de la tabla mensajes"""
        conn = self.conectar()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            m.id,
            m.conversacion_id,
            m.created_at,
            m.contenido,
            m.sql_generado,
            (SELECT contenido FROM mensajes WHERE conversacion_id = m.conversacion_id 
             AND rol = 'user' AND created_at < m.created_at 
             ORDER BY created_at DESC LIMIT 1) as pregunta_usuario
        FROM mensajes m
        WHERE m.rol = 'assistant'
          AND m.sql_generado IS NOT NULL
        ORDER BY m.created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        queries = []
        for row in rows:
            queries.append({
                'id': str(row[0]),
                'conversacion_id': str(row[1]),
                'created_at': row[2].isoformat() if row[2] else None,
                'respuesta': row[3],
                'sql_generado': row[4],
                'pregunta': row[5] or "No disponible"
            })
        
        cursor.close()
        conn.close()
        
        return queries
    
    def detectar_patron_1_left_join_filtro_on(self, sql: str) -> Tuple[bool, str]:
        """
        PATRÓN 1: LEFT JOIN con filtros temporales en ON
        Criticidad: ALTA (error 49-625%)
        """
        if 'LEFT JOIN' not in sql.upper():
            return False, ""
        
        # Buscar LEFT JOIN seguido de filtros temporales en ON
        patron = r'LEFT\s+JOIN.*?ON[^W]+?(AND\s+(EXTRACT\s*\(|DATE_TRUNC\s*\())'
        match = re.search(patron, sql, re.IGNORECASE | re.DOTALL)
        
        if match:
            return True, "LEFT JOIN con filtros temporales en ON cláusula (CRÍTICO)"
        
        return False, ""
    
    def detectar_patron_2_from_maestro_left_join(self, sql: str) -> Tuple[bool, str]:
        """
        PATRÓN 2: FROM tabla maestra + LEFT JOIN a detalles
        Criticidad: ALTA
        """
        patron = r'FROM\s+(socios|areas|clientes|proveedores)\s+\w+\s+LEFT\s+JOIN'
        match = re.search(patron, sql, re.IGNORECASE)
        
        if match:
            tabla = match.group(1)
            return True, f"Empezar FROM {tabla} (maestro) con LEFT JOIN a detalles (CRÍTICO)"
        
        return False, ""
    
    def detectar_patron_3_distribuciones_sin_filtro(self, sql: str) -> Tuple[bool, str]:
        """
        PATRÓN 3: Agregación en distribuciones sin filtro temporal
        Criticidad: MEDIA
        """
        if 'distribuciones_detalle' not in sql.lower():
            return False, ""
        
        tiene_sum = re.search(r'SUM\s*\(.*?dd\.monto', sql, re.IGNORECASE)
        tiene_filtro = re.search(r'WHERE.*?(fecha|EXTRACT|DATE_TRUNC)', sql, re.IGNORECASE)
        
        if tiene_sum and not tiene_filtro:
            return True, "Agregación en distribuciones sin filtro temporal (puede sumar todo el histórico)"
        
        return False, ""
    
    def detectar_patron_4_multiples_left_joins(self, sql: str) -> Tuple[bool, str]:
        """
        PATRÓN 4: Múltiples LEFT JOINs anidados (>2)
        Criticidad: MEDIA
        """
        count = len(re.findall(r'LEFT\s+JOIN', sql, re.IGNORECASE))
        
        if count >= 3:
            return True, f"Múltiples LEFT JOINs anidados ({count}) - complejidad alta, revisar lógica"
        
        return False, ""
    
    def detectar_patron_5_coalesce_sum_left(self, sql: str) -> Tuple[bool, str]:
        """
        PATRÓN 5: COALESCE en SUM con LEFT JOIN
        Criticidad: BAJA (puede ser correcto, revisar)
        """
        tiene_coalesce_sum = re.search(r'COALESCE\s*\(\s*SUM', sql, re.IGNORECASE)
        tiene_left_join = 'LEFT JOIN' in sql.upper()
        
        if tiene_coalesce_sum and tiene_left_join:
            return True, "COALESCE(SUM(...)) con LEFT JOIN (revisar si es necesario)"
        
        return False, ""
    
    def analizar_query(self, query: Dict) -> Dict:
        """Analiza una query y detecta todos los patrones problemáticos"""
        sql = query['sql_generado']
        problemas = []
        criticidad_maxima = "BAJA"
        
        # Detectar cada patrón
        detectores = [
            (self.detectar_patron_1_left_join_filtro_on, "ALTA"),
            (self.detectar_patron_2_from_maestro_left_join, "ALTA"),
            (self.detectar_patron_3_distribuciones_sin_filtro, "MEDIA"),
            (self.detectar_patron_4_multiples_left_joins, "MEDIA"),
            (self.detectar_patron_5_coalesce_sum_left, "BAJA")
        ]
        
        for detector, criticidad in detectores:
            detectado, descripcion = detector(sql)
            if detectado:
                problemas.append({
                    'tipo': descripcion,
                    'criticidad': criticidad
                })
                if criticidad == "ALTA":
                    criticidad_maxima = "ALTA"
                elif criticidad == "MEDIA" and criticidad_maxima != "ALTA":
                    criticidad_maxima = "MEDIA"
        
        if problemas:
            return {
                'sospechosa': True,
                'problemas': problemas,
                'criticidad': criticidad_maxima,
                'query': query
            }
        
        return {'sospechosa': False}
    
    def generar_sql_corregido(self, sql_original: str, problemas: List[Dict]) -> str:
        """Genera SQL corregido basándose en los problemas detectados"""
        sql_corregido = sql_original
        sugerencias = []
        
        for problema in problemas:
            if 'LEFT JOIN con filtros temporales en ON' in problema['tipo']:
                sugerencias.append("""
-- CORRECCIÓN: Usar INNER JOIN con filtros en WHERE
-- En lugar de:
--   FROM socios s
--   LEFT JOIN distribuciones_detalle dd ON s.id = dd.socio_id
--   LEFT JOIN operaciones o ON dd.operacion_id = o.id
--       AND EXTRACT(YEAR FROM o.fecha) = 2024

-- Usar:
--   FROM distribuciones_detalle dd
--   INNER JOIN operaciones o ON dd.operacion_id = o.id
--   INNER JOIN socios s ON dd.socio_id = s.id
--   WHERE EXTRACT(YEAR FROM o.fecha) = 2024
""")
            
            elif 'FROM' in problema['tipo'] and 'maestro' in problema['tipo']:
                sugerencias.append("""
-- CORRECCIÓN: Empezar desde tabla de detalle, no desde maestro
-- Cambiar orden de JOINs y usar INNER JOIN
""")
        
        if sugerencias:
            sql_corregido = "\n".join(sugerencias) + "\n\n" + sql_original
        
        return sql_corregido
    
    def ejecutar_validacion(self) -> Dict:
        """Ejecuta validación completa y retorna resultados"""
        print("🔍 Extrayendo queries de la base de datos...")
        queries = self.extraer_queries()
        print(f"   ✅ {len(queries)} queries encontradas\n")
        
        print("🔬 Analizando patrones problemáticos...")
        for query in queries:
            resultado = self.analizar_query(query)
            if resultado['sospechosa']:
                self.queries_sospechosas.append({
                    'id': query['id'],
                    'conversacion_id': query['conversacion_id'],
                    'fecha': query['created_at'],
                    'pregunta': query['pregunta'],
                    'respuesta_chat': query['respuesta'][:100] + '...' if len(query['respuesta']) > 100 else query['respuesta'],
                    'sql_original': query['sql_generado'],
                    'problemas': resultado['problemas'],
                    'criticidad': resultado['criticidad'],
                    'sql_corregido': self.generar_sql_corregido(
                        query['sql_generado'], 
                        resultado['problemas']
                    ),
                    'validada_manualmente': False
                })
        
        print(f"   ✅ Análisis completado\n")
        
        # Estadísticas
        stats = {
            'total_queries': len(queries),
            'queries_sospechosas': len(self.queries_sospechosas),
            'alta_criticidad': sum(1 for q in self.queries_sospechosas if q['criticidad'] == 'ALTA'),
            'media_criticidad': sum(1 for q in self.queries_sospechosas if q['criticidad'] == 'MEDIA'),
            'baja_criticidad': sum(1 for q in self.queries_sospechosas if q['criticidad'] == 'BAJA'),
            'porcentaje_correctas': round(
                ((len(queries) - len(self.queries_sospechosas)) / len(queries) * 100), 2
            ) if queries else 0
        }
        
        return {
            'queries_sospechosas': self.queries_sospechosas,
            'estadisticas': stats,
            'fecha_analisis': datetime.now().isoformat()
        }
    
    def guardar_json(self, datos: Dict, ruta: str):
        """Guarda reporte en formato JSON"""
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"   ✅ JSON guardado: {ruta}")
    
    def guardar_markdown(self, datos: Dict, ruta: str):
        """Guarda reporte en formato Markdown"""
        md = f"""# QUERIES SOSPECHOSAS - VALIDACIÓN AUTOMÁTICA
## Sistema CFO Inteligente

**Fecha de análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| **Total queries analizadas** | {datos['estadisticas']['total_queries']} |
| **Queries sospechosas** | {datos['estadisticas']['queries_sospechosas']} |
| **Alta criticidad** | 🔴 {datos['estadisticas']['alta_criticidad']} |
| **Media criticidad** | 🟡 {datos['estadisticas']['media_criticidad']} |
| **Baja criticidad** | 🟢 {datos['estadisticas']['baja_criticidad']} |
| **Porcentaje correctas** | **{datos['estadisticas']['porcentaje_correctas']}%** |

---

"""
        
        if not datos['queries_sospechosas']:
            md += "## ✅ NO SE ENCONTRARON QUERIES SOSPECHOSAS\n\n"
            md += "Todas las queries generadas siguen los patrones correctos.\n"
        else:
            md += "## 🔍 QUERIES SOSPECHOSAS DETECTADAS\n\n"
            
            for idx, query in enumerate(datos['queries_sospechosas'], 1):
                criticidad_emoji = {
                    'ALTA': '🔴',
                    'MEDIA': '🟡',
                    'BAJA': '🟢'
                }.get(query['criticidad'], '⚪')
                
                md += f"### {criticidad_emoji} QUERY SOSPECHOSA #{idx} - [{query['criticidad']}]\n\n"
                md += f"**ID:** `{query['id']}`  \n"
                md += f"**Fecha:** {query['fecha']}  \n"
                md += f"**Conversación:** `{query['conversacion_id']}`  \n\n"
                md += f"**Pregunta:**  \n> {query['pregunta']}\n\n"
                md += f"**Respuesta del chat:**  \n> {query['respuesta_chat']}\n\n"
                
                # Problemas detectados
                md += "**Problemas detectados:**\n"
                for problema in query['problemas']:
                    md += f"- {criticidad_emoji} **{problema['criticidad']}:** {problema['tipo']}\n"
                md += "\n"
                
                # SQL Original
                md += "**SQL Original (generado por Claude):**\n\n"
                md += "```sql\n"
                md += query['sql_original']
                md += "\n```\n\n"
                
                # SQL Corregido
                md += "**SQL Corregido (sugerido):**\n\n"
                md += "```sql\n"
                md += query['sql_corregido']
                md += "\n```\n\n"
                
                md += "**Acción requerida:** ⏳ Validar manualmente ejecutando ambas queries y comparando resultados\n\n"
                md += "---\n\n"
        
        # Recomendaciones
        md += "## 💡 RECOMENDACIONES\n\n"
        
        if datos['estadisticas']['alta_criticidad'] > 0:
            md += f"""### 🔴 ALTA PRIORIDAD ({datos['estadisticas']['alta_criticidad']} queries)

Queries con errores potenciales del 49-650% en resultados financieros:
1. Validar INMEDIATAMENTE con datos reales
2. Re-ejecutar con SQL corregido
3. Comparar resultados
4. Si confirma el error, actualizar prompts con ejemplos específicos

"""
        
        if datos['estadisticas']['media_criticidad'] > 0:
            md += f"""### 🟡 MEDIA PRIORIDAD ({datos['estadisticas']['media_criticidad']} queries)

Queries que requieren revisión:
1. Validar con casos de prueba
2. Verificar lógica de negocio
3. Confirmar que resultados tienen sentido

"""
        
        if datos['estadisticas']['baja_criticidad'] > 0:
            md += f"""### 🟢 BAJA PRIORIDAD ({datos['estadisticas']['baja_criticidad']} queries)

Queries que probablemente son correctas pero requieren revisión menor:
1. Revisar en tiempo libre
2. Confirmar que COALESCE es necesario
3. Optimizar si aplica

"""
        
        md += f"""## 🎯 PRÓXIMOS PASOS

1. **Ejecutar validador interactivo:**
   ```bash
   python scripts/validar_interactivo.py
   ```

2. **Revisar queries marcadas como ALTA criticidad**

3. **Actualizar prompts si se confirman errores**

4. **Re-ejecutar queries problemáticas**

---

**Reporte generado automáticamente por:** `validador_queries_automatico.py`  
**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"   ✅ Markdown guardado: {ruta}")


def main():
    """Función principal"""
    print("=" * 70)
    print("🔍 VALIDADOR AUTOMÁTICO DE QUERIES SQL - CFO INTELIGENTE")
    print("=" * 70)
    print()
    
    # Configuración
    DB_URL = "postgresql://postgres:postgres@localhost:5432/cfo_inteligente"
    OUTPUT_DIR = Path(__file__).parent.parent / "output"
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Crear validador
    validador = ValidadorQuerysAutomatico(DB_URL)
    
    try:
        # Ejecutar validación
        resultado = validador.ejecutar_validacion()
        
        # Guardar reportes
        print("\n📝 Generando reportes...")
        
        json_path = OUTPUT_DIR / "queries_sospechosas.json"
        validador.guardar_json(resultado, str(json_path))
        
        md_path = OUTPUT_DIR / "queries_sospechosas.md"
        validador.guardar_markdown(resultado, str(md_path))
        
        # Resumen
        print("\n" + "=" * 70)
        print("✅ VALIDACIÓN COMPLETADA")
        print("=" * 70)
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   • Total queries: {resultado['estadisticas']['total_queries']}")
        print(f"   • Sospechosas: {resultado['estadisticas']['queries_sospechosas']}")
        print(f"   • Alta criticidad: 🔴 {resultado['estadisticas']['alta_criticidad']}")
        print(f"   • Media criticidad: 🟡 {resultado['estadisticas']['media_criticidad']}")
        print(f"   • Baja criticidad: 🟢 {resultado['estadisticas']['baja_criticidad']}")
        print(f"   • Porcentaje correctas: {resultado['estadisticas']['porcentaje_correctas']}%")
        
        print(f"\n📁 ARCHIVOS GENERADOS:")
        print(f"   • {json_path}")
        print(f"   • {md_path}")
        
        if resultado['estadisticas']['alta_criticidad'] > 0:
            print(f"\n🚨 ADVERTENCIA: {resultado['estadisticas']['alta_criticidad']} queries de ALTA criticidad detectadas")
            print("   Ejecutar validación interactiva: python scripts/validar_interactivo.py")
        
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

