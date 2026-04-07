# Inventario completo de templates SQL — CFO Inteligente

Archivos auditados: `query_fallback.py`, `templates_gastos.py`, `templates_ingresos.py`, `templates_resumen.py`

**Reglas de validación:**
- Resultado neto = Ingresos - Gastos únicamente (NO restar retiros ni distribuciones)
- Capital de trabajo / Flujo de caja son conceptos distintos y SÍ incluyen retiros/distribuciones por diseño
- "Gastos Generales" no existe en BD; debe ser "Otros Gastos"
- Rentabilidad GLOBAL = incluir Otros Gastos | Rentabilidad POR ÁREA = excluir Otros Gastos

---

## 1. query_fallback.py

### 1.1 Templates (funciones _template_*)

| # | Función | Qué calcula | total_pesificado | deleted_at IS NULL | Resultado neto resta retiros/distrib? | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|---------|-------------|------------------|-------------------|---------------------------------------|----------------------|--------------|-----------|
| 1 | `_template_comparar_dos_años` | Ingresos, gastos, resultado, rentabilidad entre 2 años | SÍ | SÍ (en ambos UNION) | NO | NO | N/A (global) | ✅ CORRECTO |
| 2 | `_template_comparar_tres_años` | Ingresos, gastos, resultado, rentabilidad entre 3 años | SÍ | SÍ (en 3 UNION) | NO | NO | N/A (global) | ✅ CORRECTO |
| 3 | `_template_informe_año` | Ingresos, gastos, resultado por mes de un año | SÍ | SÍ | NO | NO | N/A (no rentabilidad) | ✅ CORRECTO |
| 4 | `_template_año_vs_anterior` | Delega a comparar_dos_años | — | — | — | — | — | ✅ CORRECTO (delega) |
| 5 | `_template_resumen_año` | Totales año: ingresos, gastos, resultado_neto, distribuciones, retiros, COUNT | SÍ | SÍ | NO (resultado_neto = ing-gasto) | NO | N/A | ✅ CORRECTO |
| 6 | `_template_rentabilidad_por_area_año` | Rentabilidad por área en un año | SÍ | SÍ | NO | NO | Excluye (NOT IN) | ✅ CORRECTO |
| 7 | `_template_rentabilidad_global_año` | Rentabilidad global año (todos los gastos) | SÍ | SÍ | NO | NO | Incluye (sin JOIN areas) | ✅ CORRECTO |
| 8 | `_template_comparar_trimestres` | Q1-Q4 de 2 años | SÍ | SÍ (cada UNION) | NO | NO | N/A | ✅ CORRECTO |
| 9 | `_template_comparar_semestres` | S1-S2 de 2 años | SÍ | SÍ (cada UNION) | NO | NO | N/A | ✅ CORRECTO |
| 10 | `_template_comparar_mes_entre_años` | Mismo mes en 2 años | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 11 | `_template_comparar_meses_mismo_año` | Dos meses mismo año | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 12 | `_template_comparar_trimestre_especifico` | Qn específico entre 2 años | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 13 | `_template_comparar_areas` | Compara 2 áreas específicas (parametrizadas) | SÍ | SÍ | NO | NO | N/A (áreas elegidas por usuario) | ✅ CORRECTO |
| 14 | `_template_comparar_todas_areas` | Todas las áreas operativas con rentabilidad | SÍ | SÍ | NO | NO | Excluye (NOT IN) | ✅ CORRECTO |
| 15 | `_template_informe_ejecutivo_año` | Informe completo: totales, por área, localidad, mes, retiros, distribuciones, rentab área, top clientes/proveedores | SÍ (+ total_dolarizado) | SÍ (todas CTEs) | NO en totales/por área | NO | por_area incluye todas; rentabilidad_area excluye | ✅ CORRECTO |
| 16 | `_template_comparacion_ejecutiva_años` | Comparación ejecutiva 2 años (igual estructura) | SÍ (+ total_dolarizado) | SÍ (todas CTEs) | NO | NO | Igual que anterior | ✅ CORRECTO |

### 1.2 _QUERY_PATTERNS

| # | Keywords | Qué calcula | total_pesificado | deleted_at IS NULL | Resultado neto resta retiros/distrib? | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|----------|-------------|------------------|-------------------|---------------------------------------|----------------------|--------------|-----------|
| 1 | rentabilidad por área, rentabilidad de cada área | Rentabilidad por área mes actual | SÍ | SÍ | NO | NO | Excluye (NOT IN) | ✅ CORRECTO |
| 2 | rentabilidad por localidad | Rentabilidad por localidad mes actual | SÍ | SÍ | NO | NO | N/A (localidad, no área) | ✅ CORRECTO |
| 3 | rentabilidad este mes, cuál es la rentabilidad | Rentabilidad GLOBAL mes actual | SÍ | SÍ | NO | NO | Incluye (sin JOIN) | ✅ CORRECTO |
| 4 | mercedes vs montevideo... | Ingresos y gastos por localidad | SÍ | SÍ | NO (solo ing/gas) | NO | N/A | ✅ CORRECTO |
| 5 | cómo venimos, cómo vamos | Ingresos, gastos, resultado mes actual | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 6 | cuántas operaciones, operaciones del mes | COUNT operaciones mes | N/A | SÍ | N/A | NO | N/A | ✅ CORRECTO |
| 7 | capital de trabajo, capital trabajo | Capital = ing-gast-ret-dist (por diseño) | SÍ | SÍ | SÍ (concepto distinto) | NO | N/A | ✅ CORRECTO (fórmula intencional) |
| 8 | flujo de caja, flujo caja | Entradas, salidas, flujo mes (incluye ret/dist) | SÍ | SÍ | SÍ (concepto distinto) | NO | N/A | ✅ CORRECTO (fórmula intencional) |
| 9 | tendencias, análisis tendencias | Ingresos, gastos, resultado neto últimos 12 meses | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |

### 1.3 _QUERY_COMPOUND

| # | Condiciones | Qué calcula | total_pesificado | deleted_at IS NULL | monto_uyu/monto_usd | Veredicto |
|---|-------------|-------------|------------------|-------------------|---------------------|-----------|
| 1 | retiro + mercedes | Total retiros Mercedes año (con desglose bimonetario) | SÍ (total principal) | SÍ | SÍ (componente_uyu, componente_usd para desglose) | ✅ CORRECTO (desglose justificado) |
| 2 | retiro + montevideo | Idem Montevideo | SÍ | SÍ | SÍ (desglose) | ✅ CORRECTO |

---

## 2. templates_gastos.py

### 2.1 TEMPLATES_SIMPLES (posiciones 1–15)

| # | Keywords (resumen) | Qué calcula | total_pesificado | deleted_at IS NULL | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|-------------------|-------------|------------------|-------------------|---------------------|--------------|-----------|
| 1 | gastos totales año actual | Total gastos año | SÍ | SÍ | NO | N/A (no por área) | ✅ CORRECTO |
| 2 | gastos totales mes actual | Total gastos mes | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 3 | gastos históricos | Total gastos acumulados | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 4 | gastos por área | Gastos desglosados por área (todas) | SÍ | SÍ | NO | Incluye (LEFT JOIN, todas áreas) | ✅ CORRECTO |
| 5 | gastos por localidad | Gastos por localidad | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 6 | gastos por mes | Evolución mensual gastos | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 7 | gastos por trimestre | Gastos por trimestre | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 8 | top 5 proveedores | Top 5 proveedores año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 9 | top 10 proveedores | Top 10 proveedores año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 10 | gasto promedio mensual | Promedio mensual gastos | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 11 | gastos en usd | Total gastos en dólares (total_dolarizado) | SÍ (total_dolarizado) | SÍ | NO | N/A | ✅ CORRECTO |
| 12 | cantidad de gastos | COUNT gastos año | N/A | SÍ | NO | N/A | ✅ CORRECTO |
| 13 | gasto más alto | Fila del mayor gasto (SELECT individual) | SÍ (para ORDER) | SÍ | NO | N/A | ✅ CORRECTO |
| 14 | gastos último trimestre | Total gastos trimestre anterior | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 15 | gastos último mes vs anterior | Gastos mes actual vs anterior | SÍ | SÍ | NO | N/A | ✅ CORRECTO |

### 2.2 TEMPLATES_COMPUESTOS (posiciones 16–22)

| # | Condiciones | Qué calcula | total_pesificado | deleted_at IS NULL | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|-------------|-------------|------------------|-------------------|---------------------|--------------|-----------|
| 16 | gasto + jurídica | Gastos área Jurídica | SÍ | SÍ | NO | N/A (filtro específico) | ✅ CORRECTO |
| 17 | gasto + contable | Gastos área Contable | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 18 | gasto + notarial | Gastos área Notarial | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 19 | gasto + recuperación | Gastos área Recuperación | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 20 | gasto + otros gastos | Gastos área Otros Gastos | SÍ | SÍ | NO | Correcto (a.nombre='Otros Gastos') | ✅ CORRECTO |
| 20b | gasto + gastos generales | Alias: "gastos generales" → consulta Otros Gastos | SÍ | SÍ | **En keyword solo** (SQL usa 'Otros Gastos') | Correcto en SQL | ✅ CORRECTO (alias en matching) |
| 21 | gasto + montevideo | Gastos Montevideo | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 22 | gasto + mercedes | Gastos Mercedes | SÍ | SÍ | NO | N/A | ✅ CORRECTO |

### 2.3 get_parametric_query (24–27, 23)

| # | Patrón | Qué calcula | total_pesificado | deleted_at IS NULL | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|--------|-------------|------------------|-------------------|---------------------|--------------|-----------|
| 24 | gastos [mes] [año] | Gastos de mes y año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 25 | gastos área [nombre] [año] | Gastos de área en año (_extraer_nombre_area incluye "Otros Gastos") | SÍ | SÍ | NO (mapeo → Otros Gastos) | Correcto | ✅ CORRECTO |
| 26 | top proveedores [año] | Top 10 proveedores año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 27 | gastos [localidad] [año] | Gastos de localidad en año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 23 | gasto + proveedor [X] | Gastos de proveedor específico | SÍ | SÍ | NO | N/A | ✅ CORRECTO |

---

## 3. templates_ingresos.py

### 3.1 TEMPLATES_SIMPLES (posiciones 1–15)

| # | Keywords (resumen) | Qué calcula | total_pesificado | deleted_at IS NULL | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|-------------------|-------------|------------------|-------------------|---------------------|--------------|-----------|
| 1 | ingresos totales año | Ingresos año (UYU+USD) | SÍ | SÍ | NO | N/A (ingresos, OG no aplica) | ✅ CORRECTO |
| 2 | ingresos mes actual | Ingresos mes | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 3 | ingresos históricos | Ingresos acumulados | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 4 | ingresos por área | Ingresos por área (todas) | SÍ | SÍ | NO | N/A (ingresos; OG tiene $0) | ✅ CORRECTO |
| 5 | ingresos por localidad | Ingresos por localidad | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 6 | ingresos por mes | Evolución mensual | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 7 | ingresos por trimestre | Ingresos por trimestre | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 8 | top 5 clientes | Top 5 clientes | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 9 | top 10 clientes | Top 10 clientes | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 10 | ingresos promedio mensual | Promedio mensual | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 11 | ingresos en dólares | Total ingresos USD | SÍ (total_dolarizado) | SÍ | NO | N/A | ✅ CORRECTO |
| 12 | cantidad ingresos | COUNT ingresos | N/A | SÍ | NO | N/A | ✅ CORRECTO |
| 13 | ingreso más alto | Fila mayor ingreso (col alias monto_uyu/monto_usd para display) | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 14 | ingresos último trimestre | Ingresos trimestre anterior | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 15 | ingresos mes actual vs anterior | Comparación mensual | SÍ | SÍ | NO | N/A | ✅ CORRECTO |

### 3.2 TEMPLATES_COMPUESTOS (posiciones 16–21)

| # | Condiciones | Qué calcula | total_pesificado | deleted_at IS NULL | Veredicto |
|---|-------------|-------------|------------------|-------------------|-----------|
| 16–19 | ingreso + jurídica/contable/notarial/recuperación | Ingresos por área | SÍ | SÍ | ✅ CORRECTO |
| 20–21 | ingreso + montevideo/mercedes | Ingresos por localidad | SÍ | SÍ | ✅ CORRECTO |

### 3.3 get_parametric_query (23–27, 22)

| # | Patrón | Qué calcula | total_pesificado | deleted_at IS NULL | Veredicto |
|---|--------|-------------|------------------|-------------------|-----------|
| 23 | ingresos [mes] [año], factur + cliente | Ingresos mes/año o por cliente | SÍ | SÍ | ✅ CORRECTO |
| 24 | ingresos área [nombre] [año] | Ingresos área en año | SÍ | SÍ | ✅ CORRECTO |
| 25 | top clientes [año] | Top clientes año | SÍ | SÍ | ✅ CORRECTO |
| 26 | ingresos [localidad] [año] | Ingresos localidad año | SÍ | SÍ | ✅ CORRECTO |
| 27 | ingresos por área en [localidad] | Ingresos por área en localidad | SÍ | SÍ | ✅ CORRECTO |
| 22 | factur + cliente [nombre] | Detalle ingresos cliente | SÍ (alias monto_uyu/usd para display) | SÍ | ✅ CORRECTO |

---

## 4. templates_resumen.py

### 4.1 TEMPLATES_SIMPLES (posiciones 1–17)

| # | Keywords (resumen) | Qué calcula | total_pesificado | deleted_at IS NULL | Resultado neto resta retiros/distrib? | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|-------------------|-------------|------------------|-------------------|---------------------------------------|----------------------|--------------|-----------|
| 1 | resultado neto año actual | Resultado = ing - gasto año | SÍ | SÍ | NO | NO | N/A (global) | ✅ CORRECTO |
| 2 | resultado neto mes actual | Resultado mes | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 3 | resultado neto por mes | Evolución resultado mensual | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 4 | resultado neto por área | Resultado por área (todas) | SÍ | SÍ | NO | NO | Incluye (LEFT JOIN, sin filtro OG) | ✅ CORRECTO |
| 5 | resultado neto por localidad | Resultado por localidad | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 6 | resumen general año | Ing, gas, resultado_neto, retiros, distrib, COUNT | SÍ | SÍ | NO (resultado_neto = ing-gasto) | NO | N/A | ✅ CORRECTO |
| 7 | resumen mes actual | Idem por mes | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 8 | área más rentable | Área con mayor rentabilidad (excluye OG) | SÍ | SÍ | NO | NO | Excluye (a.nombre != 'Otros Gastos') | ✅ CORRECTO |
| 9 | área con más ingresos | Área que más ingresa | SÍ | SÍ | NO | NO | Incluye (sin filtro rentab) | ✅ CORRECTO |
| 10 | área con más gastos | Área que más gasta | SÍ | SÍ | NO | NO | Incluye | ✅ CORRECTO |
| 11 | localidad más rentable | Localidad más rentable (excluye OG en cálculo) | SÍ | SÍ | NO | NO | Excluye (a.nombre != 'Otros Gastos') | ✅ CORRECTO |
| 12 | tendencias gastos | Gastos últimos 12 meses | SÍ | SÍ | N/A | NO | N/A | ✅ CORRECTO |
| 13 | tendencias resultado neto | Resultado neto últimos 12 meses | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |
| 14 | operaciones por tipo | COUNT por tipo_operacion | N/A | SÍ | N/A | NO | N/A | ✅ CORRECTO |
| 15 | proporción ingresos por área | % ingresos por área | SÍ | SÍ | N/A | NO | Incluye (todas áreas) | ✅ CORRECTO |
| 16 | proporción gastos por área | % gastos por área | SÍ | SÍ | N/A | NO | Incluye | ✅ CORRECTO |
| 17 | resumen bimonetario | Ing/gas/resultado UYU y USD | SÍ | SÍ | NO | NO | N/A | ✅ CORRECTO |

### 4.2 TEMPLATES_COMPUESTOS (posiciones 18–23)

| # | Condiciones | Qué calcula | total_pesificado | deleted_at IS NULL | Resultado neto resta? | "Gastos Generales"? | Veredicto |
|---|-------------|-------------|------------------|-------------------|-----------------------|---------------------|-----------|
| 18–19 | resultado + montevideo/mercedes | Resultado por localidad | SÍ | SÍ | NO | NO | ✅ CORRECTO |
| 20–22 | resultado + jurídica/contable/notarial | Resultado por área | SÍ | SÍ | NO | NO | ✅ CORRECTO |
| 23 | resumen + trimestre | Resumen trimestre actual (ing, gas, resultado, ret, dist) | SÍ | SÍ | NO (resultado_neto) | NO | ✅ CORRECTO |

### 4.3 get_parametric_query (24–27)

| # | Patrón | Qué calcula | total_pesificado | deleted_at IS NULL | "Gastos Generales"? | Otros Gastos | Veredicto |
|---|--------|-------------|------------------|-------------------|---------------------|--------------|-----------|
| 24 | resultado neto [año] | Resultado año parametrizado | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 25 | resumen [mes] [año] | Resumen mes/año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |
| 26 | área más rentable [año] | Área más rentable en año | SÍ | SÍ | NO | Excluye | ✅ CORRECTO |
| 27 | resultado por localidad [año] | Resultado por localidad año | SÍ | SÍ | NO | N/A | ✅ CORRECTO |

---

## Resumen final

| Archivo | Templates/Patterns | ✅ Correctos | ❌ Errores |
|---------|-------------------|-------------|------------|
| query_fallback.py | 16 funciones + 9 _QUERY_PATTERNS + 2 _QUERY_COMPOUND | 27 | 0 |
| templates_gastos.py | 15 simples + 8 compuestos + 5 paramétricos | 28 | 0 |
| templates_ingresos.py | 15 simples + 6 compuestos + 6 paramétricos | 27 | 0 |
| templates_resumen.py | 17 simples + 6 compuestos + 4 paramétricos | 27 | 0 |
| **TOTAL** | **~109 templates** | **109** | **0** |

**Nota sobre "Gastos Generales" en templates_gastos.py:** El template compuesto 20b usa la keyword "gastos generales" para el *matching*, pero el SQL generado filtra correctamente por `a.nombre = 'Otros Gastos'`. Es un alias de usuario aceptado, no un error en el SQL.
