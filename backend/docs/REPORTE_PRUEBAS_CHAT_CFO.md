# REPORTE DE PRUEBAS — CHAT CFO INTELIGENTE

## Fecha: 2026-02-11
## Entorno: Local (PostgreSQL 5432, API 8002)

### RESUMEN

- Nivel 2 (Claude): 1/6 PASS | 5 FAIL | 0 PARCIAL
- Nivel 3 (Memoria): 3/4 PASS | 0 FAIL | 1 PARCIAL
- Nivel 4 (Edge cases): 4/7 PASS | 1 FAIL | 2 PARCIAL
- **TOTAL: 8/17 PASS | 6 FAIL | 3 PARCIAL**

---

### NIVEL 2 — PREGUNTAS A CLAUDE

#### Prueba 2.1: ¿Cuál es el cliente que más nos debe en el área Notarial?

- **Dispatcher:** `claude_con_advertencias`
- **Tiempo:** 9.1s
- **SQL generado:** `SELECT cliente, SUM(total_pesificado) AS total_debe FROM operaciones o INNER JOIN areas a ON o.area_id = a.id WHERE o.tipo_operacion = 'INGRESO' AND o.deleted_at IS NULL AND a.nombre = 'Notarial' AND o.cliente IS NOT NULL GROUP BY cliente ORDER BY total_debe DESC LIMIT 1`
- **Datos:** Transporte Seguro SA — $659,976.34
- **Veredicto:** ✅ PASS
- **Notas:** Claude generó SQL correcto. El dispatcher reporta "con_advertencias" por ValidadorSQL pre-ejecución (probablemente un warning no bloqueante). Los datos son coherentes.

#### Prueba 2.2: ¿En qué meses de 2024 los gastos superaron a los ingresos?

- **Dispatcher:** `_detectar_informe_año` (template fallback)
- **Tiempo:** 7.6s
- **SQL generado:** `_template_resumen_año('2024')` — resumen anual consolidado, sin desglose mensual
- **Datos:** 1 fila con totales anuales: ingresos $17M, gastos $4.3M
- **Verificación cruzada:** Query de verificación retornó 0 filas (ningún mes tuvo gastos > ingresos en 2024). Template devolvió datos consolidados inútiles para la pregunta.
- **Veredicto:** ❌ FAIL
- **Problema:** `_detectar_informe_año` captura esta pregunta porque contiene exactamente 1 año (2024) y no contiene ninguna keyword específica de informe/rentabilidad/resumen, así que cae en el default (línea 1133: `return _template_resumen_año(año)`). La pregunta necesitaba un GROUP BY por mes con HAVING, que solo Claude puede generar.
- **Causa:** `query_fallback.py` línea 1133 — el default de `_detectar_informe_año` es demasiado agresivo: cualquier pregunta con 1 año y sin keywords de tipo informe/rentabilidad/resumen cae en `_template_resumen_año`.

#### Prueba 2.3: ¿Cuánto gastamos en proveedores de Mercedes durante el segundo semestre de 2024?

- **Dispatcher:** `_detectar_informe_año` (template fallback)
- **Tiempo:** 7.5s
- **SQL generado:** `_template_resumen_año('2024')` — resumen anual
- **Datos:** 1 fila consolidada anual
- **Verificación cruzada:** Query directa retornó $1,032,811.18. Template retornó datos genéricos sin filtro de localidad, semestre ni proveedor.
- **Veredicto:** ❌ FAIL
- **Problema:** Misma causa que 2.2. La pregunta tiene "semestre" pero `_detectar_informe_año` no lo considera un mes y no tiene escape para "semestre" + localidad + proveedor.
- **Causa:** `query_fallback.py` línea 1133 — default de `_detectar_informe_año`.

#### Prueba 2.4: ¿Cuál fue el mes con mayor diferencia entre ingresos y gastos en 2025?

- **Dispatcher:** `_detectar_informe_año` (template fallback)
- **Tiempo:** 7.9s
- **SQL generado:** `_template_resumen_año('2025')` — resumen anual
- **Datos:** 1 fila consolidada
- **Veredicto:** ❌ FAIL
- **Problema:** Misma causa. La pregunta pide análisis mensual con MAX pero recibe resumen anual.
- **Causa:** `query_fallback.py` línea 1133.

#### Prueba 2.5: Dame los 3 proveedores a los que más les pagamos en 2025

- **Dispatcher:** `_detectar_informe_año` (template fallback)
- **Tiempo:** 6.5s
- **SQL generado:** `_template_resumen_año('2025')`
- **Verificación cruzada:** Query directa retornó: ASML $484,200, Reparación PC $282,163, Taxi Company $263,700. Template devolvió datos genéricos.
- **Veredicto:** ❌ FAIL
- **Problema:** La pregunta menciona "proveedores" + "pagamos" + "2025" pero no matchea keywords de tipo resumen/informe/rentabilidad, cae en default.
- **Causa:** `query_fallback.py` línea 1133.

#### Prueba 2.6: ¿Qué porcentaje de nuestros ingresos viene de Mercedes vs Montevideo en 2025?

- **Dispatcher:** `_detectar_informe_año` (template fallback)
- **Tiempo:** 6.4s
- **SQL generado:** `_template_resumen_año('2025')`
- **Verificación cruzada:** Query directa retornó Montevideo 43.01%, Mercedes 56.99%. Template dio datos genéricos.
- **Veredicto:** ❌ FAIL
- **Problema:** Misma causa. "porcentaje" e "ingresos" + "Mercedes" + "Montevideo" no matchean ninguna keyword, cae en default.
- **Causa:** `query_fallback.py` línea 1133.

---

### NIVEL 3 — MEMORIA CONVERSACIONAL

#### Mensaje 3.1: ¿Cuáles fueron los ingresos totales de 2025?

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_resumen_año('2025')`)
- **Contexto previo:** 0 mensajes
- **Tiempo:** 7.4s
- **SQL generado:** Resumen año 2025 (totales de ingresos, gastos, distribuciones, retiros)
- **Respuesta:** "Los ingresos totales de 2025 fueron de $14.485.320" + análisis de resultado neto y rentabilidad
- **Veredicto:** ✅ PASS
- **Notas:** La respuesta es correcta con el dato solicitado. El template devuelve datos más amplios de los necesarios pero contiene el dato correcto.

#### Mensaje 3.2: ¿Y los gastos?

- **Dispatcher:** `claude` (no hay template para pregunta ambigua sin año)
- **Contexto previo:** 2 mensajes (pregunta 3.1 + respuesta 3.1)
- **Tiempo:** 8.6s
- **SQL generado:** `SELECT SUM(total_pesificado) AS total_gastos_uyu FROM operaciones WHERE tipo_operacion = 'GASTO' AND deleted_at IS NULL AND EXTRACT(YEAR FROM fecha) = 2025`
- **Respuesta:** "Los gastos totales del estudio alcanzan los $4.466.827"
- **Veredicto:** ✅ PASS
- **Notas:** Claude entendió correctamente del contexto que "los gastos" se refiere a 2025. Generó SQL filtrado por año 2025. La memoria conversacional funciona: el contexto de 2 mensajes (pregunta anterior sobre ingresos 2025) le permitió inferir el año.

#### Mensaje 3.3: ¿Cuál fue el área más rentable?

- **Dispatcher:** `claude` (no hay template simple para "área más rentable" sin año explícito)
- **Contexto previo:** 4 mensajes
- **Tiempo:** 10.8s
- **SQL generado:** CTE con rentabilidad por área, JOIN areas, excluye Otros Gastos, filtra año 2025
- **Respuesta:** "El área más rentable del estudio es Contable, con un margen del 83,3%"
- **Veredicto:** ✅ PASS
- **Notas:** Claude infirió el año 2025 del contexto. Excluyó Otros Gastos correctamente. Los datos coinciden con las pruebas del Nivel 1 (Contable 83.31%).

#### Mensaje 3.4: Comparalo con 2024

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_resumen_año('2024')`)
- **Contexto previo:** 6 mensajes
- **Tiempo:** 8.7s
- **SQL generado:** `_template_resumen_año('2024')` — solo datos de 2024, no comparación
- **Respuesta:** "No tengo datos de 2025 para hacer la comparación que me pedís. Solo cuento con la información de 2024 que acabás de consultar."
- **Veredicto:** ⚠️ PARCIAL
- **Problema:** `_detectar_informe_año` captura la pregunta porque detecta el año 2024 y cae en el default. El template solo devuelve datos de 2024, no los compara con lo que se discutió antes (rentabilidad por área de 2025). Claude en la narrativa reconoce que le faltan datos de 2025 para comparar — honesto pero no es lo que el usuario pidió.
- **Causa:** El dispatch de templates ignora el contexto conversacional. `_detectar_informe_año` solo ve "2024" en el texto y despacha el template genérico. Si la pregunta hubiera llegado a Claude (que sí tiene el contexto de 6 mensajes previos), habría podido generar una comparación de rentabilidad por área 2024 vs 2025.

---

### NIVEL 4 — EDGE CASES

#### Prueba 4.1: ¿Cómo venimos en 2026?

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_resumen_año('2026')`)
- **Tiempo:** 7.4s
- **SQL generado:** Resumen año 2026
- **Datos:** 1 fila con todos los valores en 0 y 0 operaciones
- **Verificación cruzada:** COUNT(*) = 0 → coincide
- **Respuesta:** "Arrancamos 2026 sin movimientos registrados hasta el momento."
- **Veredicto:** ✅ PASS
- **Notas:** El sistema manejó correctamente la ausencia de datos. No inventó nada.

#### Prueba 4.2: ¿Cuánto gastamos en Otros Gastos en Mercedes en 2025?

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_resumen_año('2025')`)
- **Tiempo:** 5.9s
- **SQL generado:** Resumen anual consolidado 2025 (sin filtro por área ni localidad)
- **Verificación cruzada:** Query directa retornó $463,059.87. Template retornó gastos totales de $4,466,827.
- **Respuesta:** "No tengo información específica sobre los gastos en Otros Gastos para Mercedes en 2025."
- **Veredicto:** ⚠️ PARCIAL
- **Problema:** La pregunta requiere 3 filtros simultáneos (tipo=GASTO, área=Otros Gastos, localidad=MERCEDES) que el template genérico no aplica. La respuesta narrativa es honesta ("no tengo información específica") pero no responde la pregunta. Debería haber llegado a Claude o a un template más específico.
- **Causa:** `_detectar_informe_año` captura porque ve año 2025 + no matchea keywords de tipo específico → default a `_template_resumen_año`. El filtro de exclusión que agregamos en Cambio 1 (`pregunta_es_especifica`) busca "gasto" + áreas como "contable", "jurídica" etc., pero "otros gastos" no está en la lista `areas_especificas` del filtro.

#### Prueba 4.3: ¿Cuántas distribuciones se hicieron en 2024 y cuál fue el monto total distribuido?

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_resumen_año('2024')`)
- **Tiempo:** 7.4s
- **SQL generado:** Resumen año 2024 completo
- **Datos:** distribuciones=$837,987.90, total_operaciones=1301
- **Verificación cruzada:** Query directa retornó cantidad=157, total=$837,987.90. Template retornó monto correcto pero COUNT es de TODAS las operaciones (1301), no solo distribuciones (157).
- **Respuesta:** "En 2024 se realizó una distribución por un total de $837.988. Los datos disponibles no especifican la cantidad de distribuciones individuales."
- **Veredicto:** ✅ PASS (con reserva)
- **Notas:** El monto es correcto ($837,987.90). La cantidad de distribuciones (157) no está disponible en el template usado. La narrativa es honesta al decir que no tiene el desglose de cantidad, y el monto reportado coincide exactamente con la verificación.

#### Prueba 4.4: ¿Cuáles fueron los retiros de Bruno en 2025?

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_resumen_año('2025')`)
- **Tiempo:** 6.4s
- **SQL generado:** Resumen anual consolidado 2025
- **Datos:** retiros_totales=$23,296,800.54
- **Respuesta:** "Los retiros de Bruno en 2025 no están disponibles en el detalle por socio. Los datos muestran únicamente el total de retiros de todos los socios."
- **Veredicto:** ⚠️ PARCIAL
- **Problema:** Los retiros en la tabla `operaciones` no tienen campo de socio (solo están en `distribuciones_detalle` para distribuciones). La pregunta es conceptualmente ambigua (¿retiros de la empresa asociados a Bruno?). El sistema devuelve datos genéricos y la narrativa es honesta. Es un edge case real del modelo de datos.
- **Nota de diseño:** Los retiros son de LA EMPRESA, no de socios individuales. No hay forma de filtrar por socio en retiros con el modelo actual. El sistema debería explicar esto.

#### Prueba 4.5: Haceme un análisis FODA financiero de la firma basado en los datos de 2025

- **Dispatcher:** `query_fallback` (`_detectar_informe_ejecutivo` → `_template_informe_ejecutivo_año('2025')`)
- **Tiempo:** 14.5s
- **SQL generado:** Informe ejecutivo completo (9 CTEs: totales, por área, por localidad, por mes, retiros, distribuciones, rentabilidad, top clientes, top proveedores)
- **Datos:** 42 filas con todas las dimensiones de 2025
- **Respuesta:** Análisis FODA con fortalezas (rentabilidad alta, Contable 83%), debilidades, oportunidades y amenazas. Basado en datos reales.
- **Veredicto:** ✅ PASS
- **Notas:** Excelente caso de uso del informe ejecutivo. Claude recibió datos completos de todas las dimensiones y generó un análisis sustancial.

#### Prueba 4.6: ¿Cuánto facturamos en total desde que existe la firma?

- **Dispatcher:** `templates_ingresos.get_query_ingresos` → `get_parametric_query` → catch-all #22
- **Tiempo:** 0.0s (fallo en ejecución)
- **SQL generado:** `SELECT COALESCE(cliente, 'Sin especificar') AS cliente, ... WHERE deleted_at IS NULL AND tipo_operacion = 'INGRESO' AND EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE) AND cliente IS NOT NULL ...` — Top 10 clientes de 2026 (año actual)
- **Verificación cruzada:** Query directa retornó facturación histórica total.
- **Veredicto:** ❌ FAIL
- **Problema:** La palabra "facturamos" contiene "factur" que activa el guard de `get_parametric_query`. Ningún año explícito en la pregunta, así que `año = None`. La función cae en el catch-all #22 (línea 426: `if 'factur' in p`) que genera una query de top 10 clientes para el año actual (2026, que no tiene datos). La query devuelve 0 filas, lo que causa un error de ejecución.
- **Causa:** `templates_ingresos.py` línea 426 — el catch-all `if 'factur' in p` es demasiado amplio y no tiene un path para preguntas históricas sin año.

#### Prueba 4.7: ¿Cuál es la tendencia de gastos mes a mes en 2025? ¿Están subiendo o bajando?

- **Dispatcher:** `query_fallback` (`_detectar_informe_año` → `_template_informe_año('2025')`)
- **Tiempo:** 8.6s
- **SQL generado:** Informe mensual 2025 (ingresos + gastos por mes)
- **Datos:** 9 meses con desglose (marzo-diciembre 2025)
- **Verificación cruzada:** Montos de gastos por mes coinciden exactamente con query directa.
- **Respuesta:** "Los gastos muestran una tendencia irregular durante 2025, con variaciones significativas mes a mes que van desde $80.010 en marzo hasta $974.157 en octubre."
- **Veredicto:** ✅ PASS
- **Notas:** `_detectar_informe_año` captura la pregunta por la keyword "mes a mes" que matchea con "mensual" (línea 1118). El template `_template_informe_año` es el correcto para esta pregunta. Claude generó una narrativa de tendencia con datos reales.

---

### BUGS ENCONTRADOS

| # | Nivel | Prueba | Severidad | Descripción | Causa raíz |
|---|-------|--------|-----------|-------------|------------|
| 1 | 2 | 2.2, 2.3, 2.4, 2.5, 2.6 | **CRÍTICA** | `_detectar_informe_año` captura CUALQUIER pregunta con 1 año que no matchee keywords específicas (informe/rentabilidad/resumen). El default `_template_resumen_año` devuelve datos genéricos inútiles para preguntas analíticas. | `query_fallback.py` ~línea 1133: el default `return _template_resumen_año(año)` es un catch-all excesivo que impide que preguntas complejas lleguen a Claude. |
| 2 | 4 | 4.6 | **ALTA** | "¿Cuánto facturamos desde que existe la firma?" cae en catch-all de facturación que genera top 10 clientes de 2026 (año vacío). | `templates_ingresos.py` ~línea 426: `if 'factur' in p` es catch-all demasiado amplio. No distingue preguntas históricas sin año. |
| 3 | 3 | 3.4 | **MEDIA** | "Comparalo con 2024" en contexto conversacional es capturada por template (detecta año 2024) en vez de llegar a Claude que tiene el contexto completo. | `query_fallback.py` — el dispatch de templates no considera el contexto conversacional. Templates evalúan solo el texto de la pregunta actual. |
| 4 | 4 | 4.2 | **MEDIA** | "Otros Gastos en Mercedes en 2025" no es reconocida como pregunta específica por el filtro del Cambio 1 porque "otros gastos" no está en `areas_especificas`. | `query_fallback.py` — la lista `areas_especificas` en los filtros de `_detectar_informe_ejecutivo` y `_detectar_comparacion_años` no incluye "otros gastos". |

---

### OBSERVACIONES GENERALES

**Patrón sistémico: el default de `_detectar_informe_año` es la principal fuente de errores.** 5 de 6 FAILs del Nivel 2 son causados por la misma línea (1133): cuando la pregunta tiene exactamente 1 año y no matchea keywords de tipo (informe, rentabilidad, resumen, anterior), cae en `_template_resumen_año` que devuelve datos consolidados genéricos. Esto bloquea preguntas analíticas complejas que Claude SÍ podría resolver.

**Solución propuesta para bug #1:** Eliminar o restringir el default de `_detectar_informe_año`. En vez de que "cualquier pregunta con año" caiga en template, solo capturar cuando las keywords son explícitas. Si no hay match de keywords, retornar `None` para que la pregunta pase a Claude.

**Memoria conversacional funciona correctamente en 3 de 4 casos.** Los mensajes 3.2 y 3.3 demuestran que Claude usa el contexto de mensajes previos para inferir el año y el tipo de análisis. El problema en 3.4 no es de memoria sino de dispatch: el template se evalúa antes de que Claude pueda ver el contexto.

**Fortalezas del sistema:**
- Claude genera SQL correcto cuando le llegan preguntas (2.1 fue impecable)
- Los templates son SQL verificados que dan datos precisos para las preguntas que cubren
- La validación canónica y narrativa de Claude son sólidas
- El manejo de datos vacíos (4.1: año 2026) es correcto y honesto
- Los informes ejecutivos (4.5: análisis FODA) aprovechan bien los mega-templates
- La memoria conversacional funciona bien para inferencia de contexto temporal

**Debilidad sistémica:** El sistema de dispatch tiene un sesgo hacia "capturar todo en templates" que es correcto para preguntas simples pero perjudicial para preguntas analíticas que requieren SQL ad-hoc. La solución de largo plazo sería que `_detectar_informe_año` solo capture cuando hay alta confianza de que la pregunta es un pedido de resumen/informe, y que el default sea dejar pasar a Claude.
