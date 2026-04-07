# ANÁLISIS COMBINATORIO COMPLETO DE PREGUNTAS FINANCIERAS POSIBLES
## CFO Inteligente - Conexión Consultora

**Fecha:** 2026-02-07  
**Base:** Modelo de datos verificado (operaciones, distribuciones_detalle, areas, socios)  
**Objetivo:** Mapa EXHAUSTIVO de todas las preguntas respondibles con los datos existentes

---

## PARTE 1: DIMENSIONES DE CONSULTA

### D1: TIPO DE OPERACIÓN (columna `tipo_operacion`)

| Valor | Descripción | Tiene área | Tiene cliente | Tiene proveedor | Detalle por socio |
|-------|-------------|:----------:|:-------------:|:---------------:|:-----------------:|
| INGRESO | Facturación de servicios | SÍ | SÍ | NO | NO |
| GASTO | Egresos operativos | SÍ | NO | SÍ | NO |
| RETIRO | Salida de caja empresa | NO | NO | NO | NO |
| DISTRIBUCION | Reparto utilidades a socios | NO | NO | NO | SÍ (via distribuciones_detalle) |

### D2: PERÍODO TEMPORAL (columna `fecha`)

| Granularidad | Ejemplo natural | Expresión SQL | Aplica a |
|---|---|---|---|
| Día específico | "el 15 de marzo 2025" | `fecha = '2025-03-15'` | Todos |
| Mes específico | "en marzo 2025" | `EXTRACT(MONTH FROM fecha) = 3 AND EXTRACT(YEAR FROM fecha) = 2025` | Todos |
| Mes actual | "este mes" | `DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE)` | Todos |
| Mes anterior | "el mes pasado" | `DATE_TRUNC('month', fecha) = DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'` | Todos |
| Trimestre específico | "Q1 2025", "primer trimestre" | `EXTRACT(QUARTER FROM fecha) = 1 AND EXTRACT(YEAR FROM fecha) = 2025` | Todos |
| Semestre específico | "primer semestre 2025" | `EXTRACT(MONTH FROM fecha) BETWEEN 1 AND 6 AND EXTRACT(YEAR FROM fecha) = 2025` | Todos |
| Año específico | "en 2024" | `EXTRACT(YEAR FROM fecha) = 2024` | Todos |
| Año actual | "este año" | `EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE)` | Todos |
| Últimos N meses | "últimos 3 meses" | `fecha >= CURRENT_DATE - INTERVAL 'N months'` | Todos |
| Rango de fechas | "de enero a marzo" | `fecha BETWEEN '...' AND '...'` | Todos |
| Acumulado histórico | "en total", "desde siempre" | Sin filtro temporal | Todos |
| YTD (Year-to-Date) | "en lo que va del año" | `EXTRACT(YEAR FROM fecha) = EXTRACT(YEAR FROM CURRENT_DATE) AND fecha <= CURRENT_DATE` | Todos |

**Valores temporales concretos posibles:** ~36+ (12 meses × ~3 años) + 12 trimestres + 6 semestres + 3 años + variantes dinámicas

### D3: ÁREA (columna `area_id` → tabla `areas`)

| Valor | Aplica a INGRESO | Aplica a GASTO | Aplica a RETIRO | Aplica a DISTRIBUCION |
|---|:---:|:---:|:---:|:---:|
| Jurídica | SÍ | SÍ | NO (area_id NULL) | NO (area_id NULL) |
| Notarial | SÍ | SÍ | NO | NO |
| Contable | SÍ | SÍ | NO | NO |
| Recuperación | SÍ | SÍ | NO | NO |
| Otros Gastos | NO (no tiene ingresos) | SÍ | NO | NO |
| TODAS (sin filtro) | SÍ | SÍ | N/A | N/A |

**Nota:** "Otros Gastos" se excluye de rentabilidad y de ingresos por área. Las 4 áreas operativas son: Jurídica, Notarial, Contable, Recuperación.

### D4: LOCALIDAD (columna `localidad`)

| Valor | Aplica a | Notas |
|---|---|---|
| MONTEVIDEO | Todos los tipos | Valor ENUM en mayúsculas |
| MERCEDES | Todos los tipos | Valor ENUM en mayúsculas |
| AMBAS (sin filtro) | Todos los tipos | Default cuando no se especifica |

### D5: MONEDA / PRESENTACIÓN MONETARIA

| Modo | Campo(s) SQL | Cuándo usar | Aplica a |
|---|---|---|---|
| Pesificado (default) | `total_pesificado` | "¿Cuánto?" sin especificar moneda | Todos |
| Dolarizado | `total_dolarizado` | "¿Cuánto en dólares?" (total convertido) | Todos |
| Componente UYU | `monto_uyu` | "¿Cuánto fue en pesos?" (solo parte UYU) | Todos |
| Componente USD | `monto_usd` | "¿Cuánto fue en dólares originales?" (solo parte USD) | Todos |
| Ambos componentes | `monto_uyu, monto_usd` | "¿Cuánto en pesos y cuánto en dólares?" | Todos |
| Proporción moneda | `COUNT(CASE WHEN moneda_original='USD'...)` | "¿Qué % fue en dólares?" | Todos |
| Monto original | `monto_original, moneda_original` | "¿Cuál fue el monto original?" | Detalle por operación |
| Bimoneda completo | `total_pesificado, total_dolarizado` | Informes ejecutivos | Todos |

**5 modos de presentación estándar + 3 especiales = 8 variantes monetarias**

### D6: CLIENTE (columna `cliente`, solo INGRESO)

| Valor | Notas |
|---|---|
| Cliente específico (N valores) | VARCHAR libre, cardinalidad variable |
| Todos (sin filtro) | Default |
| Sin especificar (NULL) | Operaciones sin cliente asignado |

### D7: PROVEEDOR (columna `proveedor`, solo GASTO)

| Valor | Notas |
|---|---|
| Proveedor específico (M valores) | VARCHAR libre, cardinalidad variable |
| Todos (sin filtro) | Default |
| Sin especificar (NULL) | Operaciones sin proveedor asignado |

### D8: SOCIO (tabla `distribuciones_detalle` → `socios`, solo DISTRIBUCION)

| Valor | Porcentaje |
|---|---|
| Agustina | 20% |
| Viviana | 20% |
| Gonzalo | 20% |
| Pancho | 20% |
| Bruno | 20% |
| TODOS (sin filtro) | 100% |

---

## PARTE 2: TIPOS DE AGREGACIÓN

### A1: SUMATORIAS (SUM)
- Total de montos (en cualquier presentación monetaria)
- Subtotales por grupo (área, localidad, mes, etc.)
- Acumulados

### A2: CONTEO (COUNT)
- Cantidad de operaciones
- Cantidad de operaciones por tipo
- Cantidad de clientes distintos (COUNT DISTINCT)
- Cantidad de proveedores distintos
- Cantidad de distribuciones

### A3: PROMEDIO (AVG)
- Monto promedio por operación
- Facturación promedio mensual
- Gasto promedio mensual
- Ticket promedio por cliente
- Distribución promedio por socio

### A4: MÍNIMO (MIN)
- Operación de menor monto
- Mes de menor facturación
- Área de menor ingreso

### A5: MÁXIMO (MAX)
- Operación de mayor monto
- Mes de mayor facturación
- Mejor área

### A6: RANKINGS (TOP N / BOTTOM N)
- Top N clientes por facturación
- Top N proveedores por gasto
- Top N meses más productivos
- Bottom N áreas por rentabilidad
- Mejor/peor mes
- Mejor/peor área

### A7: COMPARACIONES (A vs B)
- Año vs año (2024 vs 2025)
- Mes vs mes (marzo vs abril)
- Mismo mes diferente año (enero 2024 vs enero 2025)
- Trimestre vs trimestre
- Semestre vs semestre
- Área vs área (Jurídica vs Contable)
- Localidad vs localidad (Montevideo vs Mercedes)
- Este período vs anterior

### A8: TENDENCIAS / EVOLUCIÓN TEMPORAL
- Evolución mes a mes (ingresos, gastos, resultado)
- Evolución trimestral
- Evolución interanual
- Tendencia de rentabilidad
- Tendencia por área

### A9: PROPORCIONES (% del total)
- % de facturación por área
- % de facturación por localidad
- % de gastos por área
- % de operaciones en USD vs UYU
- % que representa cada socio (siempre 20%)
- % de retiros vs distribuciones vs resultado neto
- Concentración de clientes (% de top clientes)

### A10: PROYECCIONES
- Proyección anual basada en ritmo actual
- Proyección de resultado neto
- Proyección de rentabilidad
- "Si mantenemos este ritmo..."

### A11: CÁLCULOS DERIVADOS / RATIOS
- **Rentabilidad:** (Ingresos - Gastos) / Ingresos × 100
- **Resultado neto:** Ingresos - Gastos
- **Capital de trabajo:** Ingresos - Gastos - Retiros - Distribuciones
- **Flujo de caja:** Entradas - Salidas (todas)
- **Margen por operación:** Resultado / Cantidad operaciones
- **Crecimiento interanual:** (Año2 - Año1) / Año1 × 100
- **Variación mes a mes:** (MesN - MesN-1) / MesN-1 × 100

### A12: LISTADOS / DETALLE
- Listar operaciones de un período
- Listar distribuciones por socio
- Listar retiros por localidad
- Última operación registrada

---

## PARTE 3: MATRIZ DE COMBINACIONES

### 3.1 INGRESO — Combinaciones posibles

**Dimensiones aplicables:**
- Temporal: 12 granularidades × N valores concretos (~50 combinaciones útiles)
- Área: 6 opciones (5 áreas + todas)
- Localidad: 3 opciones
- Moneda: 5 modos estándar
- Cliente: N+1 opciones (estimado ~50+1)

**Agregaciones aplicables:** SUM, COUNT, AVG, MIN, MAX, TOP N, BOTTOM N, %, tendencia, proyección, comparación

#### Cálculo de combinaciones base (SUM simple):
```
Moneda(5) × Temporal(50) × Área(6) × Localidad(3) = 4,500 combinaciones de totales
+ Cliente específico: × 51 = +229,500 (la mayoría irrelevantes en la práctica)
```

#### Combinaciones de comparación temporal:
```
Par de años: C(3,2) = 3 pares × Área(6) × Localidad(3) × Moneda(5) = 270
Par de meses: C(12,2) = 66 pares por año × 3 años × Moneda(5) = 990
Mismo mes entre años: 12 meses × 3 pares × Moneda(5) = 180
Trimestres entre años: 4 × 3 × 5 = 60
Semestres entre años: 2 × 3 × 5 = 30
Total comparaciones temporales: ~1,530
```

#### Combinaciones de comparación entre dimensiones:
```
Área vs Área: C(5,2) = 10 × Temporal(50) × Moneda(5) = 2,500
Localidad vs Localidad: 1 × Temporal(50) × Moneda(5) = 250
Total comparaciones dimensión: ~2,750
```

#### Rankings:
```
Top clientes: Temporal(50) × Área(6) × Localidad(3) × Moneda(5) × TopN(3: 1,3,5,10) = 13,500
Top áreas: Temporal(50) × Localidad(3) × Moneda(5) × TopN(3) = 2,250
Top meses: Área(6) × Localidad(3) × Moneda(5) × TopN(3) = 270
Total rankings: ~16,020
```

#### Proporciones:
```
% por área: Temporal(50) × Localidad(3) × Moneda(5) = 750
% por localidad: Temporal(50) × Área(6) × Moneda(5) = 1,500
% moneda: Temporal(50) × Área(6) × Localidad(3) = 900
Total proporciones: ~3,150
```

#### Tendencias:
```
Mensual: Área(6) × Localidad(3) × Moneda(5) = 90
Trimestral: 90
Interanual: 90
Total tendencias: ~270
```

#### Proyecciones:
```
Anual: Área(6) × Localidad(3) × Moneda(5) = 90
Total proyecciones: ~90
```

**TOTAL INGRESO: ~28,310+ combinaciones teóricas**  
**Combinaciones PRÁCTICAS (que un socio realmente preguntaría): ~200-300**

---

### 3.2 GASTO — Combinaciones posibles

**Dimensiones aplicables:** Igual que INGRESO pero con Proveedor en lugar de Cliente, y área "Otros Gastos" incluida en gastos.

- Temporal: ~50 valores
- Área: 6 opciones (5 áreas + todas, incluyendo Otros Gastos)
- Localidad: 3 opciones
- Moneda: 5 modos
- Proveedor: M+1 opciones (~30+1)

#### Cálculo base (SUM):
```
Moneda(5) × Temporal(50) × Área(6) × Localidad(3) = 4,500
+ Proveedor: × 31 = +139,500 (mayormente irrelevantes)
```

**Estructura de combinaciones idéntica a INGRESO** reemplazando Cliente por Proveedor.

**TOTAL GASTO: ~25,000+ combinaciones teóricas**  
**Combinaciones PRÁCTICAS: ~200-300**

---

### 3.3 RETIRO — Combinaciones posibles

**Dimensiones aplicables:**
- Temporal: ~50 valores
- Localidad: 3 opciones (MUY RELEVANTE para retiros)
- Moneda: 5 modos (MUY RELEVANTE: retiros pueden ser en UYU o USD)
- **SIN área, SIN cliente, SIN proveedor, SIN socio**

#### Cálculo base:
```
Moneda(5) × Temporal(50) × Localidad(3) = 750
Comparaciones temporales: ~100
Rankings: ~50
Proporciones (% por localidad, % por moneda): ~100
Tendencias: ~30
```

**TOTAL RETIRO: ~1,030 combinaciones teóricas**  
**Combinaciones PRÁCTICAS: ~50-80**

---

### 3.4 DISTRIBUCION — Combinaciones posibles

**Dimensiones aplicables:**
- Temporal: ~50 valores
- Socio: 6 opciones (5 socios + todos)
- Moneda: 5 modos
- **SIN área, SIN localidad significativa, SIN cliente, SIN proveedor**

#### Cálculo base:
```
Moneda(5) × Temporal(50) × Socio(6) = 1,500
Comparaciones temporales por socio: ~300
Rankings (top socio — siempre igual 20%): ~10
Proporciones: ~50
Tendencias por socio: ~60
```

**TOTAL DISTRIBUCION: ~1,920 combinaciones teóricas**  
**Combinaciones PRÁCTICAS: ~60-100**

---

### 3.5 COMBINACIONES CRUZADAS (entre tipos de operación)

Estas son las preguntas más valiosas:

#### Rentabilidad (INGRESO vs GASTO):
```
Global: Temporal(50) × Moneda(5) = 250
Por área: Temporal(50) × Área(4, sin Otros Gastos) × Moneda(5) = 1,000
Por localidad: Temporal(50) × Localidad(3) × Moneda(5) = 750
Por área + localidad: Temporal(50) × Área(4) × Localidad(3) × Moneda(5) = 3,000
Comparación temporal de rentabilidad: ~500
Total rentabilidad: ~5,500
```

#### Resultado neto (INGRESO - GASTO):
```
Misma estructura que rentabilidad: ~5,500
```

#### Capital de trabajo (INGRESO - GASTO - RETIRO - DISTRIBUCION):
```
Temporal(50) × Moneda(5) = 250
Por localidad (parcial): ~100
Total: ~350
```

#### Flujo de caja (entradas vs salidas):
```
Temporal(50) × Moneda(5) = 250
Por localidad: ~150
Total: ~400
```

#### Informes ejecutivos (multi-dimensión):
```
Por año: Años(3) × Moneda(2 principales) = 6
Comparación 2 años: C(3,2) = 3 × Moneda(2) = 6
Total ejecutivos: ~12
```

**TOTAL CRUZADAS: ~12,000+ combinaciones teóricas**  
**Combinaciones PRÁCTICAS: ~150-250**

---

### 3.6 RESUMEN NUMÉRICO DE COMBINACIONES

| Tipo | Teóricas | Prácticas (estimado) |
|---|---:|---:|
| INGRESO | 28,310 | 250 |
| GASTO | 25,000 | 250 |
| RETIRO | 1,030 | 70 |
| DISTRIBUCION | 1,920 | 80 |
| CRUZADAS (Rentabilidad, Capital, Flujo) | 12,000 | 200 |
| **TOTAL** | **~68,260** | **~850** |

---

## PARTE 4: CATÁLOGO COMPLETO DE FAMILIAS DE PREGUNTAS

### FAMILIA 1: TOTAL DE INGRESOS (Facturación)
- **Ejemplo:** "¿Cuánto facturamos en 2025?" / "¿Cuáles fueron los ingresos de este mes?"
- **Campos SQL:** `SUM(total_pesificado)` o `SUM(total_dolarizado)`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'INGRESO'`, filtro temporal, `deleted_at IS NULL`
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Hay queries canónicas para 2024, 2025, mes actual. No hay template genérico para cualquier mes/trimestre.

### FAMILIA 2: TOTAL DE GASTOS
- **Ejemplo:** "¿Cuánto gastamos en 2025?" / "¿Cuáles fueron los gastos del Q3?"
- **Campos SQL:** `SUM(total_pesificado)` o `SUM(total_dolarizado)`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'GASTO'`, filtro temporal, `deleted_at IS NULL`
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Hay canónicas para 2024, 2025. No para mes específico ni trimestre.

### FAMILIA 3: TOTAL DE RETIROS
- **Ejemplo:** "¿Cuánto se retiró en 2025?" / "¿Cuántos retiros hubo este mes?"
- **Campos SQL:** `SUM(total_pesificado)`, `COUNT(*)`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'RETIRO'`, filtro temporal, `deleted_at IS NULL`
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Hay canónica para retiros 2025. Hay compound para retiro+localidad.

### FAMILIA 4: TOTAL DE DISTRIBUCIONES (Global)
- **Ejemplo:** "¿Cuánto se distribuyó en 2025?" / "¿Total distribuido este año?"
- **Campos SQL:** `SUM(total_pesificado)` desde `operaciones`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'DISTRIBUCION'`, filtro temporal, `deleted_at IS NULL`
- **Complejidad:** SIMPLE
- **¿Template en fallback?** SÍ — Canónica para 2024 y 2025.

### FAMILIA 5: DISTRIBUCIONES POR SOCIO
- **Ejemplo:** "¿Cuánto recibió Bruno en 2025?" / "¿Cuánto le tocó a Agustina?"
- **Campos SQL:** `SUM(dd.total_pesificado)`, `SUM(dd.total_dolarizado)`
- **Tablas:** `distribuciones_detalle` JOIN `operaciones` JOIN `socios`
- **Filtros:** `s.nombre = 'Bruno'`, filtro temporal, `o.deleted_at IS NULL`
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Compound query para cada socio (5 templates), pero solo para año actual.

### FAMILIA 6: DESGLOSE DE DISTRIBUCIONES (todos los socios)
- **Ejemplo:** "¿Cuánto recibió cada socio en 2025?" / "Detalle de distribuciones por socio"
- **Campos SQL:** `s.nombre`, `SUM(dd.total_pesificado)`, `SUM(dd.total_dolarizado)`
- **Tablas:** `distribuciones_detalle` JOIN `operaciones` JOIN `socios`
- **Filtros:** filtro temporal, `o.deleted_at IS NULL`
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — El informe ejecutivo incluye esto, pero no como query independiente.

### FAMILIA 7: INGRESOS POR ÁREA
- **Ejemplo:** "¿Cuánto facturó Jurídica en 2025?" / "Ingresos por área este trimestre"
- **Campos SQL:** `a.nombre`, `SUM(o.total_pesificado)`
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** `tipo_operacion = 'INGRESO'`, `a.nombre = '...'` o GROUP BY, filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Canónica para Jurídica, Notarial, Contable en 2025. No para Recuperación ni otros períodos.

### FAMILIA 8: GASTOS POR ÁREA
- **Ejemplo:** "¿Cuánto gastó el área Contable?" / "Gastos por área en 2024"
- **Campos SQL:** `a.nombre`, `SUM(o.total_pesificado)`
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** `tipo_operacion = 'GASTO'`, filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO

### FAMILIA 9: INGRESOS POR LOCALIDAD
- **Ejemplo:** "¿Cuánto facturamos en Montevideo en 2025?" / "Ingresos Mercedes vs Montevideo"
- **Campos SQL:** `SUM(total_pesificado)`, `localidad`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'INGRESO'`, `localidad = '...'`, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Canónica para MVD y MER 2025. Hay pattern "mercedes vs montevideo" pero solo mes actual.

### FAMILIA 10: GASTOS POR LOCALIDAD
- **Ejemplo:** "¿Cuánto gastamos en Mercedes?" / "Gastos por localidad 2025"
- **Campos SQL:** `SUM(total_pesificado)`, `localidad`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'GASTO'`, `localidad`, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** NO

### FAMILIA 11: RETIROS POR LOCALIDAD
- **Ejemplo:** "¿Cuánto se retiró en Mercedes?" / "Retiros de Montevideo este año"
- **Campos SQL:** `SUM(total_pesificado)`, `localidad`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'RETIRO'`, `localidad`, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** SÍ — Compound para retiro+mercedes y retiro+montevideo (año actual).

### FAMILIA 12: INGRESOS POR CLIENTE
- **Ejemplo:** "¿Cuánto facturamos al cliente X?" / "Top clientes de 2025"
- **Campos SQL:** `cliente`, `SUM(total_pesificado)`, `COUNT(*)`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'INGRESO'`, `cliente = '...'` o GROUP BY, filtro temporal
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** PARCIAL — Informe ejecutivo tiene top 10, pero no query independiente.

### FAMILIA 13: GASTOS POR PROVEEDOR
- **Ejemplo:** "¿Cuánto le pagamos al proveedor Y?" / "Top proveedores 2025"
- **Campos SQL:** `proveedor`, `SUM(total_pesificado)`, `COUNT(*)`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'GASTO'`, `proveedor = '...'` o GROUP BY, filtro temporal
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** PARCIAL — Informe ejecutivo tiene top 10, pero no query independiente.

### FAMILIA 14: RENTABILIDAD GLOBAL
- **Ejemplo:** "¿Cuál es la rentabilidad de este mes?" / "¿Cuál es el margen de 2025?"
- **Campos SQL:** `(SUM(CASE INGRESO) - SUM(CASE GASTO)) / NULLIF(SUM(CASE INGRESO), 0) * 100`
- **Tablas:** `operaciones`
- **Filtros:** filtro temporal, `deleted_at IS NULL`
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Pattern "rentabilidad este mes" + Canónica para 2025 y mes actual.

### FAMILIA 15: RENTABILIDAD POR ÁREA
- **Ejemplo:** "¿Cuál es la rentabilidad de Jurídica?" / "Rentabilidad por área 2025"
- **Campos SQL:** `a.nombre`, fórmula rentabilidad
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** `a.nombre != 'Otros Gastos'`, filtro temporal
- **Complejidad:** MEDIA-COMPLEJA
- **¿Template en fallback?** SÍ — Pattern "rentabilidad por área" (mes actual) + Template parametrizado por año.

### FAMILIA 16: RENTABILIDAD POR LOCALIDAD
- **Ejemplo:** "¿Cuál es la rentabilidad de Montevideo?" / "¿Mercedes es rentable?"
- **Campos SQL:** `localidad`, fórmula rentabilidad
- **Tablas:** `operaciones`
- **Filtros:** `localidad`, filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Pattern "rentabilidad por localidad" (mes actual). No para año específico.

### FAMILIA 17: RESULTADO NETO
- **Ejemplo:** "¿Cuál es el resultado de este mes?" / "Resultado neto 2025"
- **Campos SQL:** `SUM(CASE INGRESO) - SUM(CASE GASTO)`
- **Tablas:** `operaciones`
- **Filtros:** filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Dentro del template "cómo venimos" (mes actual) y resumen año.

### FAMILIA 18: CAPITAL DE TRABAJO
- **Ejemplo:** "¿Cuál es el capital de trabajo?" / "¿Cuánto queda en caja?"
- **Campos SQL:** `SUM(INGRESO) - SUM(GASTO) - SUM(RETIRO) - SUM(DISTRIBUCION)`
- **Tablas:** `operaciones`
- **Filtros:** Acumulado total o filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Pattern "capital de trabajo" (acumulado) + Canónica para 2025.

### FAMILIA 19: FLUJO DE CAJA
- **Ejemplo:** "¿Cuál es el flujo de caja de este mes?" / "Flujo de caja 2025"
- **Campos SQL:** Entradas (INGRESO) vs Salidas (GASTO+RETIRO+DISTRIBUCION)
- **Tablas:** `operaciones`
- **Filtros:** filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Pattern "flujo de caja" (mes actual). No para año o trimestre específico.

### FAMILIA 20: CONTEO DE OPERACIONES
- **Ejemplo:** "¿Cuántas operaciones hubo este mes?" / "Cantidad de ingresos en 2025"
- **Campos SQL:** `COUNT(*)`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Pattern "operaciones del mes" + Canónica operaciones 2025.

### FAMILIA 21: CONTEO POR DIMENSIÓN
- **Ejemplo:** "¿Cuántos ingresos por área?" / "¿Cuántas operaciones por localidad?"
- **Campos SQL:** `COUNT(*)`, GROUP BY dimensión
- **Tablas:** `operaciones` (JOIN `areas` si por área)
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** NO

### FAMILIA 22: PROMEDIO DE MONTO
- **Ejemplo:** "¿Cuál es el promedio de facturación mensual?" / "Ticket promedio"
- **Campos SQL:** `AVG(total_pesificado)` o `SUM/COUNT por período`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** NO

### FAMILIA 23: MÍNIMO / MÁXIMO
- **Ejemplo:** "¿Cuál fue el mes con mayor facturación?" / "¿Cuál fue el gasto más alto?"
- **Campos SQL:** `MAX(total_pesificado)`, `MIN(total_pesificado)`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** NO

### FAMILIA 24: TOP CLIENTES
- **Ejemplo:** "¿Quiénes son los 5 mejores clientes?" / "Top clientes de 2025"
- **Campos SQL:** `cliente`, `SUM(total_pesificado)`, `ORDER BY DESC LIMIT N`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'INGRESO'`, `cliente IS NOT NULL`, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Dentro de informe ejecutivo (top 10). No como query independiente parametrizable.

### FAMILIA 25: TOP PROVEEDORES
- **Ejemplo:** "¿A quién le pagamos más?" / "Top proveedores 2025"
- **Campos SQL:** `proveedor`, `SUM(total_pesificado)`, `ORDER BY DESC LIMIT N`
- **Tablas:** `operaciones`
- **Filtros:** `tipo_operacion = 'GASTO'`, `proveedor IS NOT NULL`, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Dentro de informe ejecutivo (top 10). No como query independiente.

### FAMILIA 26: TOP ÁREAS POR INGRESO/RENTABILIDAD
- **Ejemplo:** "¿Cuál es el área más rentable?" / "¿Qué área factura más?"
- **Campos SQL:** `a.nombre`, SUM o fórmula rentabilidad, `ORDER BY DESC LIMIT N`
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** filtro temporal, excluir Otros Gastos
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Template "rentabilidad_por_area_año" ordena por rentabilidad.

### FAMILIA 27: PROPORCIÓN POR ÁREA
- **Ejemplo:** "¿Qué porcentaje del ingreso viene de Jurídica?" / "Peso de cada área"
- **Campos SQL:** `SUM(area) / SUM(total) * 100`
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO

### FAMILIA 28: PROPORCIÓN POR LOCALIDAD
- **Ejemplo:** "¿Qué porcentaje facturamos en Montevideo?" / "Peso de Mercedes"
- **Campos SQL:** `SUM(localidad) / SUM(total) * 100`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO

### FAMILIA 29: PROPORCIÓN POR MONEDA
- **Ejemplo:** "¿Qué porcentaje de ingresos fue en dólares?" / "Peso del USD"
- **Campos SQL:** `COUNT(CASE WHEN moneda_original='USD') * 100.0 / COUNT(*)`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, filtro temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** NO

### FAMILIA 30: TENDENCIA MENSUAL
- **Ejemplo:** "¿Cómo evolucionó la facturación mes a mes?" / "Tendencia de gastos"
- **Campos SQL:** `DATE_TRUNC('month', fecha)`, `SUM(...)` GROUP BY mes
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, filtro temporal (últimos N meses o año)
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** SÍ — Pattern "tendencias" (últimos 12 meses de ingresos). No para gastos/resultado.

### FAMILIA 31: TENDENCIA TRIMESTRAL
- **Ejemplo:** "¿Cómo fue trimestre a trimestre en 2025?"
- **Campos SQL:** `EXTRACT(QUARTER FROM fecha)`, `SUM(...)`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, año
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Template "comparar_trimestres" entre 2 años. No para un solo año.

### FAMILIA 32: COMPARACIÓN AÑO VS AÑO
- **Ejemplo:** "Comparar 2024 vs 2025" / "¿Crecimos respecto al año pasado?"
- **Campos SQL:** Ingresos/Gastos/Resultado por año
- **Tablas:** `operaciones`
- **Filtros:** años específicos
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Templates parametrizados para 2 y 3 años + año vs anterior.

### FAMILIA 33: COMPARACIÓN MES VS MES (mismo año)
- **Ejemplo:** "Comparar marzo vs abril 2025"
- **Campos SQL:** Ingresos/Gastos por mes
- **Tablas:** `operaciones`
- **Filtros:** meses y año específicos
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Template parametrizado.

### FAMILIA 34: COMPARACIÓN MISMO MES ENTRE AÑOS
- **Ejemplo:** "Enero 2024 vs enero 2025"
- **Campos SQL:** Ingresos/Gastos del mes en cada año
- **Tablas:** `operaciones`
- **Filtros:** mes y años específicos
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Template parametrizado.

### FAMILIA 35: COMPARACIÓN TRIMESTRES ENTRE AÑOS
- **Ejemplo:** "Comparar trimestres de 2024 y 2025" / "Q1 2024 vs Q1 2025"
- **Campos SQL:** Ingresos/Gastos por trimestre por año
- **Tablas:** `operaciones`
- **Filtros:** años y trimestres
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Templates para todos los trimestres y para trimestre específico.

### FAMILIA 36: COMPARACIÓN SEMESTRES ENTRE AÑOS
- **Ejemplo:** "Primer semestre 2024 vs primer semestre 2025"
- **Campos SQL:** Ingresos/Gastos por semestre por año
- **Tablas:** `operaciones`
- **Filtros:** años y semestres
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Template parametrizado.

### FAMILIA 37: COMPARACIÓN ÁREA VS ÁREA
- **Ejemplo:** "Comparar Jurídica vs Contable" / "¿Cuál rinde más, Jurídica o Notarial?"
- **Campos SQL:** Ingresos/Gastos/Rentabilidad por área
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** áreas específicas, año actual
- **Complejidad:** MEDIA
- **¿Template en fallback?** SÍ — Template para 2 áreas y comparar todas las áreas.

### FAMILIA 38: COMPARACIÓN LOCALIDAD VS LOCALIDAD
- **Ejemplo:** "Montevideo vs Mercedes" / "¿Dónde facturamos más?"
- **Campos SQL:** Ingresos/Gastos por localidad
- **Tablas:** `operaciones`
- **Filtros:** ambas localidades, filtro temporal
- **Complejidad:** SIMPLE-MEDIA
- **¿Template en fallback?** SÍ — Pattern "mercedes vs montevideo" (mes actual). No para año específico.

### FAMILIA 39: "CÓMO VENIMOS" / ESTADO ACTUAL
- **Ejemplo:** "¿Cómo venimos este mes?" / "¿Cómo vamos?"
- **Campos SQL:** SUM Ingresos, Gastos, Resultado del mes actual
- **Tablas:** `operaciones`
- **Filtros:** mes actual
- **Complejidad:** SIMPLE
- **¿Template en fallback?** SÍ — Pattern estático "cómo venimos".

### FAMILIA 40: PROYECCIÓN ANUAL
- **Ejemplo:** "¿Si seguimos así, cuánto facturaremos este año?" / "Proyección 2025"
- **Campos SQL:** `SUM(total_pesificado) / EXTRACT(MONTH FROM CURRENT_DATE) * 12`
- **Tablas:** `operaciones`
- **Filtros:** año actual
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO (se delega a Chain-of-Thought SQL)

### FAMILIA 41: INFORME EJECUTIVO DE UN AÑO
- **Ejemplo:** "Informe del 2024" / "Resumen ejecutivo 2025" / "Análisis detallado 2024"
- **Campos SQL:** Multi-CTE con totales, por área, por localidad, por mes, retiros, distribuciones, rentabilidad, top clientes, top proveedores
- **Tablas:** `operaciones`, `areas`, `distribuciones_detalle`, `socios`
- **Filtros:** año específico
- **Complejidad:** COMPLEJA
- **¿Template en fallback?** SÍ — Template ejecutivo completo (9 secciones).

### FAMILIA 42: COMPARACIÓN EJECUTIVA ENTRE AÑOS
- **Ejemplo:** "Comparar 2024 vs 2025 completo" / "Análisis 2024 contra 2025"
- **Campos SQL:** Multi-CTE con todas las dimensiones × 2 años
- **Tablas:** `operaciones`, `areas`, `distribuciones_detalle`, `socios`
- **Filtros:** dos años
- **Complejidad:** COMPLEJA
- **¿Template en fallback?** SÍ — Template de comparación ejecutiva (9 secciones × 2 años).

### FAMILIA 43: INFORME MENSUAL DE UN AÑO
- **Ejemplo:** "Desglose mes a mes de 2025" / "Informe mensual 2024"
- **Campos SQL:** Mes, Ingresos, Gastos, Resultado GROUP BY mes
- **Tablas:** `operaciones`
- **Filtros:** año específico
- **Complejidad:** SIMPLE
- **¿Template en fallback?** SÍ — Template "_template_informe_año".

### FAMILIA 44: RESUMEN TOTALES DE UN AÑO
- **Ejemplo:** "¿Cuánto en total en 2024?" / "Resumen de totales 2025"
- **Campos SQL:** Ingresos, Gastos, Resultado, Distribuciones, Retiros, Count
- **Tablas:** `operaciones`
- **Filtros:** año específico
- **Complejidad:** SIMPLE
- **¿Template en fallback?** SÍ — Template "_template_resumen_año".

### FAMILIA 45: INGRESOS POR ÁREA + LOCALIDAD (cruce)
- **Ejemplo:** "¿Cuánto facturó Jurídica en Montevideo?" / "Ingresos Contable Mercedes 2025"
- **Campos SQL:** `SUM(total_pesificado)` con JOIN areas y filtro localidad
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** tipo_operacion, area, localidad, temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO

### FAMILIA 46: GASTOS POR ÁREA + LOCALIDAD (cruce)
- **Ejemplo:** "¿Cuánto gastó Notarial en Mercedes?"
- **Campos SQL:** `SUM(total_pesificado)` con filtros múltiples
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** tipo_operacion, area, localidad, temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO

### FAMILIA 47: RENTABILIDAD POR ÁREA + PERÍODO ESPECÍFICO (cruce)
- **Ejemplo:** "Rentabilidad de Jurídica en Q1 2025" / "Margen Contable marzo 2025"
- **Campos SQL:** Fórmula rentabilidad con filtro área + temporal
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** area, temporal específico
- **Complejidad:** MEDIA-COMPLEJA
- **¿Template en fallback?** PARCIAL — Template por año, no por mes ni trimestre.

### FAMILIA 48: CRECIMIENTO INTERANUAL
- **Ejemplo:** "¿Cuánto crecimos en facturación de 2024 a 2025?" / "Variación % gastos"
- **Campos SQL:** `(SUM_año2 - SUM_año1) / SUM_año1 * 100`
- **Tablas:** `operaciones`
- **Filtros:** dos años, tipo_operacion
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Los templates de comparación incluyen montos pero no calculan el % de variación explícitamente.

### FAMILIA 49: VARIACIÓN MES A MES
- **Ejemplo:** "¿Cuánto varió la facturación respecto al mes pasado?"
- **Campos SQL:** Comparación mes actual vs anterior
- **Tablas:** `operaciones`
- **Filtros:** mes actual y anterior
- **Complejidad:** MEDIA
- **¿Template en fallback?** NO

### FAMILIA 50: CONCENTRACIÓN DE CLIENTES
- **Ejemplo:** "¿Qué porcentaje del ingreso viene de los top 5 clientes?" / "Dependencia de clientes"
- **Campos SQL:** SUM top 5 / SUM total * 100
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion = INGRESO, temporal
- **Complejidad:** COMPLEJA
- **¿Template en fallback?** NO

### FAMILIA 51: RETIROS POR MONEDA
- **Ejemplo:** "¿Cuánto se retiró en dólares?" / "Retiros en pesos vs dólares"
- **Campos SQL:** `SUM(monto_uyu)`, `SUM(monto_usd)`, o filtro por `moneda_original`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion = RETIRO, moneda_original o componentes
- **Complejidad:** SIMPLE
- **¿Template en fallback?** PARCIAL — Compound retiro+localidad incluye componentes. Informe ejecutivo incluye retiros por moneda.

### FAMILIA 52: RETIROS POR LOCALIDAD + MONEDA (cruce)
- **Ejemplo:** "¿Cuánto se retiró en dólares en Mercedes?" / "Retiros USD Montevideo"
- **Campos SQL:** `SUM(monto_usd)`, localidad, moneda_original
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion = RETIRO, localidad, moneda_original
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Informe ejecutivo sección retiros_empresa cubre esto.

### FAMILIA 53: DISTRIBUCIONES POR SOCIO + PERÍODO
- **Ejemplo:** "¿Cuánto recibió Bruno en Q1 2025?" / "Distribuciones de Agustina en marzo"
- **Campos SQL:** `SUM(dd.total_pesificado)` con filtros socio + temporal
- **Tablas:** `distribuciones_detalle` JOIN `operaciones` JOIN `socios`
- **Filtros:** socio, temporal específico
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Compound solo para año actual, no para mes/trimestre específico.

### FAMILIA 54: TENDENCIA DE DISTRIBUCIONES POR SOCIO
- **Ejemplo:** "¿Cómo evolucionaron las distribuciones de Bruno?" / "Historial de distribuciones"
- **Campos SQL:** `DATE_TRUNC('month', o.fecha)`, `SUM(dd.total_pesificado)` GROUP BY mes
- **Tablas:** `distribuciones_detalle` JOIN `operaciones` JOIN `socios`
- **Filtros:** socio (opcional), temporal
- **Complejidad:** MEDIA-COMPLEJA
- **¿Template en fallback?** NO

### FAMILIA 55: LISTADO DE ÚLTIMAS OPERACIONES
- **Ejemplo:** "¿Cuáles fueron los últimos ingresos?" / "Últimas 10 operaciones"
- **Campos SQL:** `SELECT *` con ORDER BY fecha DESC LIMIT N
- **Tablas:** `operaciones` (JOIN `areas` si se quiere nombre)
- **Filtros:** tipo_operacion (opcional), temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** NO

### FAMILIA 56: CLIENTES ÚNICOS / PROVEEDORES ÚNICOS
- **Ejemplo:** "¿Cuántos clientes distintos tenemos?" / "¿Cuántos proveedores?"
- **Campos SQL:** `COUNT(DISTINCT cliente)`, `COUNT(DISTINCT proveedor)`
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** NO

### FAMILIA 57: INGRESOS POR ÁREA + CLIENTE (cruce profundo)
- **Ejemplo:** "¿Cuánto facturó Jurídica al cliente X?" / "Top clientes de Contable"
- **Campos SQL:** `SUM(total_pesificado)` con area + cliente
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** area, cliente, temporal
- **Complejidad:** COMPLEJA
- **¿Template en fallback?** NO

### FAMILIA 58: GASTOS POR ÁREA + PROVEEDOR (cruce profundo)
- **Ejemplo:** "¿Cuánto le pagó Jurídica al proveedor Y?"
- **Campos SQL:** `SUM(total_pesificado)` con area + proveedor
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** area, proveedor, temporal
- **Complejidad:** COMPLEJA
- **¿Template en fallback?** NO

### FAMILIA 59: COMPARACIÓN TEMPORAL POR ÁREA
- **Ejemplo:** "¿Cómo le fue a Jurídica en 2024 vs 2025?" / "Evolución de Contable"
- **Campos SQL:** Ingresos/Gastos por área × período
- **Tablas:** `operaciones` JOIN `areas`
- **Filtros:** area específica, dos períodos
- **Complejidad:** MEDIA-COMPLEJA
- **¿Template en fallback?** PARCIAL — Comparación ejecutiva incluye por área, pero no individual.

### FAMILIA 60: COMPARACIÓN TEMPORAL POR LOCALIDAD
- **Ejemplo:** "¿Cómo le fue a Montevideo en 2024 vs 2025?"
- **Campos SQL:** Ingresos/Gastos por localidad × período
- **Tablas:** `operaciones`
- **Filtros:** localidad, dos períodos
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — Comparación ejecutiva incluye por localidad, no individual.

### FAMILIA 61: TIPO DE CAMBIO PROMEDIO
- **Ejemplo:** "¿Cuál fue el tipo de cambio promedio de las operaciones en USD?"
- **Campos SQL:** `AVG(tipo_cambio)` WHERE moneda_original = 'USD'
- **Tablas:** `operaciones`
- **Filtros:** moneda_original, temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** NO

### FAMILIA 62: OPERACIONES POR MONEDA ORIGINAL
- **Ejemplo:** "¿Cuántas operaciones fueron en dólares?" / "Mix de monedas"
- **Campos SQL:** `COUNT(*)`, `moneda_original` GROUP BY
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion (opcional), temporal
- **Complejidad:** SIMPLE
- **¿Template en fallback?** NO

### FAMILIA 63: ESTACIONALIDAD
- **Ejemplo:** "¿Cuál es nuestro mejor mes históricamente?" / "¿Hay estacionalidad?"
- **Campos SQL:** `EXTRACT(MONTH FROM fecha)`, `AVG(SUM(...))` multi-año
- **Tablas:** `operaciones`
- **Filtros:** tipo_operacion, multi-año
- **Complejidad:** COMPLEJA
- **¿Template en fallback?** NO

### FAMILIA 64: RESUMEN MULTI-TIPO (dashboard)
- **Ejemplo:** "¿Cuál es el panorama general?" / "Resumen de todo"
- **Campos SQL:** Ingresos + Gastos + Resultado + Retiros + Distribuciones + Capital
- **Tablas:** `operaciones`
- **Filtros:** temporal
- **Complejidad:** MEDIA
- **¿Template en fallback?** PARCIAL — "cómo venimos" cubre parcialmente. Resumen año es más completo.

---

## PARTE 5: ESTIMACIÓN NUMÉRICA

### Inventario de templates actuales en `query_fallback.py`

#### Templates parametrizados (funciones):
| # | Template | Qué cubre |
|---|---|---|
| 1 | `_template_comparar_dos_años` | 2 años: ingresos, gastos, resultado, rentabilidad |
| 2 | `_template_comparar_tres_años` | 3 años: mismas métricas |
| 3 | `_template_informe_año` | Desglose mensual de un año |
| 4 | `_template_año_vs_anterior` | Año vs año anterior |
| 5 | `_template_resumen_año` | Totales de un año (todas las métricas) |
| 6 | `_template_rentabilidad_por_area_año` | Rentabilidad por área de un año |
| 7 | `_template_comparar_trimestres` | 4 trimestres × 2 años |
| 8 | `_template_comparar_semestres` | 2 semestres × 2 años |
| 9 | `_template_comparar_mes_entre_años` | Mismo mes entre 2 años |
| 10 | `_template_comparar_meses_mismo_año` | 2 meses del mismo año |
| 11 | `_template_comparar_trimestre_especifico` | Q específico entre 2 años |
| 12 | `_template_comparar_areas` | 2 áreas entre sí (año actual) |
| 13 | `_template_comparar_todas_areas` | Todas las áreas (año actual) |
| 14 | `_template_informe_ejecutivo_año` | Informe completo 9 secciones |
| 15 | `_template_comparacion_ejecutiva_años` | Comparación completa 2 años |

#### Queries estáticas (patterns):
| # | Pattern | Qué cubre |
|---|---|---|
| 16 | Rentabilidad por área | Mes actual |
| 17 | Rentabilidad por localidad | Mes actual |
| 18 | Rentabilidad general | Mes actual |
| 19 | Mercedes vs Montevideo | Mes actual |
| 20 | Cómo venimos | Mes actual: ingresos, gastos, resultado |
| 21 | Operaciones del mes | COUNT mes actual |
| 22 | Capital de trabajo | Acumulado total |
| 23 | Flujo de caja | Mes actual |
| 24 | Tendencias | Últimos 12 meses de ingresos |

#### Queries compuestas (compound):
| # | Compound | Qué cubre |
|---|---|---|
| 25 | Retiro + Mercedes | Total retiros Mercedes año actual |
| 26 | Retiro + Montevideo | Total retiros Montevideo año actual |
| 27 | Distribución + Bruno | Total distribuciones Bruno año actual |
| 28 | Distribución + Agustina | Total distribuciones Agustina año actual |
| 29 | Distribución + Viviana | Total distribuciones Viviana año actual |
| 30 | Distribución + Gonzalo | Total distribuciones Gonzalo año actual |
| 31 | Distribución + Pancho | Total distribuciones Pancho año actual |

**TOTAL: 31 templates/patterns**

### Cobertura adicional: Queries canónicas (validación)

Las queries canónicas en `canonical_queries_config.py` no generan SQL, pero validan resultados para:
- Facturación 2024, 2025, mes actual
- Gastos 2024, 2025
- Rentabilidad 2025, mes actual
- Capital de trabajo
- Facturación por localidad (MVD, MER) 2025
- Facturación por área (Jurídica, Notarial, Contable) 2025
- Distribuciones 2024, 2025
- Retiros 2025
- Cantidad operaciones 2025

**Total canónicas: 18 validaciones**

### Resumen de cobertura

| Métrica | Valor |
|---|---|
| **Total familias de preguntas identificadas** | **64** |
| **Total combinaciones teóricas** | **~68,260** |
| **Combinaciones prácticas (preguntas reales)** | **~850** |
| **Templates/patterns en fallback** | **31** |
| **Familias con cobertura TOTAL en fallback** | **14** (F4-DISTRIB global, F5, F11, F14, F15, F16 parcial, F18, F19, F32-36, F37, F39, F41-44) |
| **Familias con cobertura PARCIAL** | **18** (F1, F2, F3, F6, F7, F9, F12, F13, F17, F24, F25, F26, F30, F38, F47, F48, F51-53) |
| **Familias SIN cobertura en fallback** | **32** (F8, F10, F21-23, F27-29, F40, F45-46, F49-50, F54-64) |
| **% familias cubiertas totalmente** | **22%** (14/64) |
| **% familias cubiertas parcialmente** | **28%** (18/64) |
| **% familias sin cobertura** | **50%** (32/64) |

**NOTA IMPORTANTE:** Las familias sin cobertura en el fallback NO necesariamente fallan. Claude (el generador de SQL por IA) puede generar SQL correcto para MUCHAS de estas familias. El fallback solo es la red de seguridad para preguntas comunes.

---

## PARTE 6: PREGUNTAS BIMONETARIAS ESPECIALES

### 6.1 VARIANTES PARA INGRESOS (Facturación)

| # | Pregunta | Campo SQL | Tipo |
|---|---|---|---|
| 1 | "¿Cuánto facturamos?" | `SUM(total_pesificado)` | Default pesificado |
| 2 | "¿Cuánto facturamos en dólares?" | `SUM(total_dolarizado)` | Total dolarizado |
| 3 | "¿Cuánto de la facturación fue originalmente en dólares?" | `SUM(monto_usd) WHERE moneda_original='USD'` | Componente USD |
| 4 | "¿Cuánto de la facturación fue originalmente en pesos?" | `SUM(monto_uyu) WHERE moneda_original='UYU'` | Componente UYU |
| 5 | "¿Cuánto facturamos en pesos y cuánto en dólares?" | `SUM(monto_uyu), SUM(monto_usd)` | Ambos componentes |
| 6 | "¿Qué porcentaje de la facturación fue en dólares?" | `COUNT(WHERE USD) * 100.0 / COUNT(*)` | Proporción por conteo |
| 7 | "¿Qué peso tiene el dólar en nuestra facturación?" | `SUM(monto_usd * tipo_cambio) / SUM(total_pesificado)` | Proporción por monto |
| 8 | "Facturación pesificada y dolarizada" | `SUM(total_pesificado), SUM(total_dolarizado)` | Bimoneda completo |

**Cada una de estas 8 variantes se combina con CADA filtro temporal, área, localidad y cliente → 8 × 850/4 ≈ 1,700 variantes adicionales**

### 6.2 VARIANTES PARA GASTOS

| # | Pregunta | Campo SQL | Tipo |
|---|---|---|---|
| 1 | "¿Cuánto gastamos?" | `SUM(total_pesificado)` | Default pesificado |
| 2 | "¿Cuánto gastamos en dólares?" | `SUM(total_dolarizado)` | Total dolarizado |
| 3 | "¿Cuánto de los gastos fue originalmente en dólares?" | `SUM(monto_usd) WHERE moneda_original='USD'` | Componente USD |
| 4 | "¿Cuánto de los gastos fue en pesos?" | `SUM(monto_uyu) WHERE moneda_original='UYU'` | Componente UYU |
| 5 | "¿Cuánto gastamos en pesos y cuánto en dólares?" | `SUM(monto_uyu), SUM(monto_usd)` | Ambos componentes |
| 6 | "¿Qué porcentaje de los gastos fue en dólares?" | `COUNT(WHERE USD) * 100.0 / COUNT(*)` | Proporción por conteo |
| 7 | "¿Qué peso tiene el dólar en nuestros gastos?" | Proporción por monto | Proporción por monto |
| 8 | "Gastos pesificados y dolarizados" | `SUM(total_pesificado), SUM(total_dolarizado)` | Bimoneda completo |

### 6.3 VARIANTES PARA RETIROS

| # | Pregunta | Campo SQL | Tipo |
|---|---|---|---|
| 1 | "¿Cuánto se retiró?" | `SUM(total_pesificado)` | Default pesificado |
| 2 | "¿Cuánto se retiró en dólares?" (dolarizado) | `SUM(total_dolarizado)` | Total dolarizado |
| 3 | "¿Cuánto se retiró en dólares?" (componente) | `SUM(monto_usd)` | Componente USD |
| 4 | "¿Cuánto se retiró en pesos?" (componente) | `SUM(monto_uyu)` | Componente UYU |
| 5 | "¿Cuánto se retiró en pesos y cuánto en dólares?" | `SUM(monto_uyu), SUM(monto_usd)` | Ambos componentes |
| 6 | "¿Qué porcentaje de los retiros fue en dólares?" | `COUNT(WHERE USD) * 100.0 / COUNT(*)` | Proporción |
| 7 | "Retiros pesificados y dolarizados" | `SUM(total_pesificado), SUM(total_dolarizado)` | Bimoneda |

**NOTA AMBIGÜEDAD CRÍTICA en retiros:** "¿Cuánto se retiró en dólares?" puede significar:
- (a) Total dolarizado: `SUM(total_dolarizado)` — todo convertido a USD
- (b) Componente USD: `SUM(monto_usd)` — solo la parte que fue originalmente en USD
- El sistema debe distinguir por contexto o pedir clarificación.

### 6.4 VARIANTES PARA DISTRIBUCIONES (Global)

| # | Pregunta | Campo SQL |
|---|---|---|
| 1 | "¿Cuánto se distribuyó?" | `SUM(total_pesificado)` desde operaciones |
| 2 | "¿Cuánto se distribuyó en dólares?" | `SUM(total_dolarizado)` desde operaciones |
| 3 | "¿Cuánto se distribuyó en pesos y en dólares?" | `SUM(monto_uyu), SUM(monto_usd)` |
| 4 | "Distribuciones pesificadas y dolarizadas" | `SUM(total_pesificado), SUM(total_dolarizado)` |

### 6.5 VARIANTES PARA DISTRIBUCIONES POR SOCIO

Para CADA socio (5), las siguientes variantes:

| # | Pregunta | Campo SQL |
|---|---|---|
| 1 | "¿Cuánto recibió [Socio]?" | `SUM(dd.total_pesificado)` |
| 2 | "¿Cuánto recibió [Socio] en dólares?" | `SUM(dd.total_dolarizado)` |
| 3 | "¿Cuánto recibió [Socio] en pesos y en dólares?" | `SUM(dd.monto_uyu), SUM(dd.monto_usd)` |
| 4 | "¿Cuánto recibió [Socio] pesificado y dolarizado?" | `SUM(dd.total_pesificado), SUM(dd.total_dolarizado)` |

**Total por socio: 4 variantes × 5 socios = 20 preguntas base**
**Con filtro temporal: 20 × ~10 períodos relevantes = 200 variantes**

### 6.6 VARIANTES BIMONETARIAS CRUZADAS

| # | Pregunta | Campos | Complejidad |
|---|---|---|---|
| 1 | "¿Cuál es la rentabilidad en dólares?" | total_dolarizado para ingresos y gastos | MEDIA |
| 2 | "¿Cuál es el resultado neto en dólares?" | `SUM(total_dolarizado)` por tipo | MEDIA |
| 3 | "¿Cuál es el capital de trabajo en dólares?" | `SUM(total_dolarizado)` todos los tipos | MEDIA |
| 4 | "¿Flujo de caja en dólares?" | `SUM(total_dolarizado)` entradas vs salidas | MEDIA |
| 5 | "¿Cuánto del resultado fue en operaciones USD?" | Filtro moneda_original + cálculo | COMPLEJA |

**Total variantes bimonetarias especiales: ~45 familias × 8 modos = ~360 variantes únicas**

---

## PARTE 7: GAPS CRÍTICOS

### NIVEL 1: GAPS MUY PROBABLES (preguntas que los socios SEGURAMENTE harán)

| # | Familia | Ejemplo de pregunta | ¿Tiene template? | Riesgo |
|---|---|---|---|---|
| **G1** | **Gastos por área** | "¿Cuánto gastó Jurídica este mes?" | NO | ALTO — pregunta básica, ningún template |
| **G2** | **Gastos por localidad** | "¿Cuánto gastamos en Mercedes?" | NO | ALTO — solo hay ingresos por localidad |
| **G3** | **Promedio mensual** | "¿Cuál es el promedio de facturación mensual?" | NO | ALTO — pregunta ejecutiva frecuente |
| **G4** | **Proyección anual** | "¿Si seguimos así, cuánto facturaremos este año?" | NO en fallback (hay CoT) | MEDIO — depende de Claude + Chain-of-Thought |
| **G5** | **Desglose distribuciones** | "¿Cuánto recibió cada socio este año?" | PARCIAL (solo individual) | MEDIO — no hay template grupal con temporal |
| **G6** | **Top clientes standalone** | "¿Quiénes son nuestros mejores clientes?" | NO (solo en ejecutivo) | ALTO — pregunta muy frecuente |
| **G7** | **Top proveedores standalone** | "¿A quién le pagamos más?" | NO (solo en ejecutivo) | ALTO — pregunta frecuente |
| **G8** | **Proporción por área** | "¿Qué porcentaje de los ingresos viene de Jurídica?" | NO | MEDIO — pregunta de composición |
| **G9** | **Proporción por localidad** | "¿Qué porcentaje facturamos en Montevideo?" | NO | MEDIO — pregunta de composición |
| **G10** | **Proporción por moneda** | "¿Qué porcentaje de la facturación fue en USD?" | NO | ALTO — tema bimonetario frecuente |
| **G11** | **Variación mes a mes** | "¿Crecimos o caímos respecto al mes pasado?" | NO | ALTO — pregunta ejecutiva frecuente |
| **G12** | **Resultado neto standalone** | "¿Cuál es el resultado de este mes?" | PARCIAL (dentro de "cómo venimos") | BAJO — "cómo venimos" lo cubre |
| **G13** | **Clientes/proveedores únicos** | "¿Cuántos clientes tenemos?" | NO | MEDIO — pregunta operativa |

### NIVEL 2: GAPS MODERADAMENTE PROBABLES

| # | Familia | Ejemplo | ¿Template? | Riesgo |
|---|---|---|---|---|
| G14 | Flujo de caja por período | "Flujo de caja de 2025" (no solo mes actual) | NO | MEDIO |
| G15 | Capital de trabajo temporal | "Capital de trabajo a diciembre 2025" | PARCIAL | BAJO |
| G16 | Conteo por dimensión | "¿Cuántos ingresos por área?" | NO | BAJO |
| G17 | Últimas operaciones | "¿Cuáles fueron los últimos ingresos?" | NO | MEDIO |
| G18 | Comparación temporal por área | "¿Cómo le fue a Jurídica en 2024 vs 2025?" | PARCIAL | MEDIO |
| G19 | Área + Localidad cruce | "¿Cuánto facturó Jurídica en MVD?" | NO | MEDIO |
| G20 | Crecimiento % interanual | "¿Cuánto crecimos en %?" | PARCIAL | MEDIO |
| G21 | Tendencia de gastos | "¿Cómo evolucionaron los gastos?" | NO (solo ingresos) | ALTO |
| G22 | Tendencia de resultado | "¿Cómo evolucionó el resultado?" | NO | ALTO |
| G23 | Mínimo/Máximo | "¿Cuál fue el mes con mayor facturación?" | NO | MEDIO |
| G24 | Distribuciones por socio + período específico | "¿Cuánto recibió Bruno en Q1?" | NO | MEDIO |

### NIVEL 3: GAPS MENOS PROBABLES PERO POSIBLES

| # | Familia | Ejemplo | ¿Template? |
|---|---|---|---|
| G25 | Estacionalidad | "¿Cuál es nuestro mejor mes?" | NO |
| G26 | Concentración de clientes | "¿Dependemos de pocos clientes?" | NO |
| G27 | Tipo de cambio promedio | "¿Cuál fue el TC promedio?" | NO |
| G28 | Área + cliente cruce | "Top clientes de Jurídica" | NO |
| G29 | Área + proveedor cruce | "Gastos de Jurídica por proveedor" | NO |
| G30 | Tendencia distribuciones socio | "Historial de distribuciones de Bruno" | NO |
| G31 | Comparación Mercedes vs MVD año específico | "MVD vs MER en 2024" | NO (solo mes actual) |
| G32 | Rentabilidad por localidad + período | "Rentabilidad de MVD en 2024" | NO (solo mes actual) |

### RESUMEN DE GAPS

| Nivel | Gaps | Impacto |
|---|---|---|
| **Nivel 1 (Muy probable)** | **13 gaps** | Preguntas que los socios HACEN regularmente |
| **Nivel 2 (Moderado)** | **11 gaps** | Preguntas ocasionales de análisis |
| **Nivel 3 (Menos probable)** | **8 gaps** | Preguntas de análisis avanzado |
| **TOTAL** | **32 gaps** | |

### TOP 10 GAPS MÁS CRÍTICOS (priorizar implementación):

1. **G1: Gastos por área** — Pregunta básica sin ninguna cobertura
2. **G2: Gastos por localidad** — Asimetría (ingresos sí tiene, gastos no)
3. **G6: Top clientes standalone** — Pregunta muy frecuente de socios
4. **G7: Top proveedores standalone** — Complemento natural
5. **G10: Proporción por moneda** — Tema bimonetario fundamental
6. **G11: Variación mes a mes** — KPI ejecutivo esencial
7. **G21: Tendencia de gastos** — Solo hay tendencia de ingresos
8. **G22: Tendencia de resultado** — Evolución del bottom line
9. **G3: Promedio mensual** — Métrica ejecutiva frecuente
10. **G31: MVD vs MER por año** — Hoy solo cubre mes actual

---

## APÉNDICE A: MAPA DE COBERTURA ACTUAL

### Lo que SÍ cubre el fallback (31 templates):

```
COMPARACIONES TEMPORALES:
├── 2 años (ingresos + gastos + resultado + rentabilidad)        ✅
├── 3 años (mismas métricas)                                       ✅
├── Año vs anterior                                                ✅
├── Trimestres entre 2 años (todos)                                ✅
├── Trimestre específico entre 2 años                              ✅
├── Semestres entre 2 años                                         ✅
├── Mismo mes entre 2 años                                         ✅
└── 2 meses del mismo año                                          ✅

INFORMES:
├── Resumen totales de un año                                      ✅
├── Desglose mensual de un año                                     ✅
├── Rentabilidad por área de un año                                ✅
├── Informe ejecutivo completo (9 secciones)                       ✅
└── Comparación ejecutiva 2 años (9 secciones × 2)                ✅

COMPARACIONES POR DIMENSIÓN:
├── 2 áreas entre sí                                               ✅
├── Todas las áreas                                                ✅
└── Mercedes vs Montevideo (mes actual)                            ✅

MÉTRICAS DEL MES ACTUAL:
├── Rentabilidad global                                            ✅
├── Rentabilidad por área                                          ✅
├── Rentabilidad por localidad                                     ✅
├── Cómo venimos (ingresos, gastos, resultado)                     ✅
├── Operaciones del mes (count)                                    ✅
└── Flujo de caja                                                  ✅

ACUMULADOS:
└── Capital de trabajo                                             ✅

TENDENCIAS:
└── Ingresos últimos 12 meses                                      ✅

RETIROS:
├── Retiros Mercedes (año actual)                                  ✅
└── Retiros Montevideo (año actual)                                ✅

DISTRIBUCIONES POR SOCIO:
├── Bruno (año actual)                                             ✅
├── Agustina (año actual)                                          ✅
├── Viviana (año actual)                                           ✅
├── Gonzalo (año actual)                                           ✅
└── Pancho (año actual)                                            ✅
```

### Lo que NO cubre el fallback y depende 100% de Claude:

```
TOTALES SIMPLES:
├── Gastos por área                                                ❌
├── Gastos por localidad                                           ❌
├── Ingresos por área + localidad (cruce)                          ❌
├── Gastos por área + localidad (cruce)                            ❌
└── Retiros por moneda (sin localidad)                             ❌

RANKINGS STANDALONE:
├── Top N clientes                                                 ❌
├── Top N proveedores                                              ❌
├── Top áreas por ingreso (sin rentabilidad)                       ❌
└── Mejor/peor mes                                                 ❌

PROPORCIONES:
├── % por área                                                     ❌
├── % por localidad                                                ❌
├── % por moneda                                                   ❌
└── Concentración de clientes                                      ❌

PROMEDIOS:
├── Promedio mensual de facturación                                ❌
├── Ticket promedio por cliente                                    ❌
├── Gasto promedio por operación                                   ❌
└── Distribución promedio por socio                                ❌

TENDENCIAS (que NO sean ingresos 12 meses):
├── Tendencia de gastos                                            ❌
├── Tendencia de resultado                                         ❌
├── Tendencia por área                                             ❌
├── Tendencia trimestral                                           ❌
└── Tendencia de distribuciones                                    ❌

VARIACIONES:
├── Variación mes a mes                                            ❌
├── Crecimiento % interanual                                       ❌
└── Variación trimestral                                           ❌

LISTADOS:
├── Últimas N operaciones                                          ❌
├── Clientes únicos                                                ❌
└── Proveedores únicos                                             ❌

PROYECCIONES:
├── Proyección anual                                               ❌ (delegado a CoT)
└── Proyección por área                                            ❌

DISTRIBUCIONES AVANZADAS:
├── Desglose todos los socios (query independiente)                ❌
├── Socio + período específico (mes/trimestre)                     ❌
└── Tendencia distribuciones por socio                             ❌

CRUCES PROFUNDOS:
├── Área + cliente                                                 ❌
├── Área + proveedor                                               ❌
├── Localidad + período específico (comparación)                   ❌
├── Área + período específico (comparación)                        ❌
└── Estacionalidad                                                 ❌

BIMONETARIOS ESPECIALES:
├── Cualquier total en modo dolarizado                             ❌
├── Componentes UYU/USD separados                                  ❌
├── Proporción por moneda                                          ❌
├── Rentabilidad en dólares                                        ❌
└── Capital de trabajo en dólares                                  ❌

MISCELÁNEOS:
├── Tipo de cambio promedio                                        ❌
├── MVD vs MER para año específico                                 ❌
├── Rentabilidad por localidad para año específico                 ❌
└── Flujo de caja para período no-mes-actual                       ❌
```

---

## APÉNDICE B: RESUMEN EJECUTIVO DE COBERTURA

```
╔══════════════════════════════════════════════════════════════════╗
║                    RESUMEN DE COBERTURA                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Total familias de preguntas:         64                         ║
║  Cubiertas TOTAL por fallback:        14  (22%)                  ║
║  Cubiertas PARCIAL por fallback:      18  (28%)                  ║
║  Sin cobertura fallback:              32  (50%)                  ║
║                                                                  ║
║  Templates en query_fallback.py:      31                         ║
║  Queries canónicas (validación):      18                         ║
║                                                                  ║
║  Combinaciones teóricas totales:      ~68,260                    ║
║  Combinaciones prácticas:             ~850                       ║
║  Cubiertas por fallback:              ~120  (14% de prácticas)   ║
║  Dependen de Claude:                  ~730  (86% de prácticas)   ║
║                                                                  ║
║  Gaps CRÍTICOS (Nivel 1):             13                         ║
║  Gaps MODERADOS (Nivel 2):            11                         ║
║  Gaps BAJOS (Nivel 3):                8                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### Interpretación:

1. **El fallback cubre las preguntas MÁS comunes** (comparaciones anuales, informes ejecutivos, rentabilidad del mes, distribuciones por socio).

2. **Los gaps más críticos** son preguntas BÁSICAS que faltan: gastos por área/localidad, top clientes/proveedores standalone, proporciones, promedios, y tendencias de gastos/resultado.

3. **Claude cubre el 86%** de las preguntas prácticas. Esto funciona bien CUANDO Claude genera SQL correcto, pero no hay garantía al 100%.

4. **La mayor vulnerabilidad** está en preguntas bimonetarias complejas y cruces de múltiples dimensiones, donde la ambigüedad del lenguaje natural puede llevar a SQL incorrecto.

5. **Prioridad de implementación:** Los 10 gaps críticos del Nivel 1 cubrirían las preguntas más frecuentes que hoy dependen 100% de Claude sin red de seguridad.
