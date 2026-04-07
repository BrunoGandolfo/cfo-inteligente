# Inventario de templates SQL — Catálogo CFO Inteligente

Origen: `backend/app/services/templates_catalog.py` (157 templates en 6 categorías).

## INGRESOS
ING-001: Detalle de ingresos (fecha, descripción, montos) de un cliente específico por nombre exacto (entre comillas)
ING-002: Suma de ingresos UYU y USD de un área en una localidad en un año dado
ING-003: Suma de ingresos UYU y USD de un área en un año dado
ING-004: Total de ingresos en USD de un año; opcionalmente filtrado por área
ING-005: Ingresos UYU, USD y cantidad de operaciones de un área en dos años para comparar
ING-006: Cantidad de operaciones y totales UYU/USD por mes en un año
ING-007: Suma de ingresos UYU y USD de un mes concreto de un año
ING-008: Suma de ingresos UYU y USD de todo un año
ING-009: Listado de hasta 10 clientes con más ingresos en un año (UYU, USD, cantidad)
ING-010: Suma de ingresos UYU y USD de Montevideo o Mercedes en un año
ING-011: Ingresos UYU y USD por área dentro de una localidad en el año actual
ING-012: Clientes con totales UYU/USD y cantidad de operaciones; año paramétrico o actual; límite 10
ING-013: Suma de ingresos UYU y USD del área Jurídica en el año actual
ING-014: Suma de ingresos UYU y USD del área Contable en el año actual
ING-015: Suma de ingresos UYU y USD del área Notarial en el año actual
ING-016: Suma de ingresos UYU y USD del área Recuperación en el año actual
ING-017: Suma de ingresos UYU y USD en localidad Montevideo en el año actual
ING-018: Suma de ingresos UYU y USD en localidad Mercedes en el año actual
ING-019: La operación de ingreso de mayor monto del año (fecha, descripción, cliente, montos)
ING-020: Los 5 clientes con más ingresos en el año actual (UYU, USD, cantidad)
ING-021: Los 10 clientes con más ingresos en el año actual (UYU, USD, cantidad)
ING-022: Comparación de ingresos UYU y USD entre mes actual y mes anterior
ING-023: Suma de ingresos UYU y USD del trimestre anterior al actual
ING-024: Evolución mensual de ingresos UYU y USD por mes del año actual
ING-025: Ingresos UYU y USD por trimestre (Q1-Q4) del año actual
ING-026: Ingresos UYU y USD por localidad (Montevideo, Mercedes) en el año actual
ING-027: Ingresos UYU y USD desglosados por área en el año actual
ING-028: Promedio de ingresos UYU y USD por mes en el año actual
ING-029: Total de ingresos en USD del año actual
ING-030: Número de operaciones de ingreso en el año actual
ING-031: Suma de ingresos UYU y USD del mes en curso
ING-032: Suma total de ingresos UYU y USD del año en curso
ING-033: Suma acumulada de todos los ingresos (toda la historia)

## GASTOS
GAS-001: Total y cantidad de gastos de un proveedor por nombre (año actual o paramétrico)
GAS-002: Gastos UYU, USD y cantidad de operaciones de un área en dos años
GAS-003: Total de gastos en USD de un año; opcionalmente por área
GAS-004: Suma de gastos de un mes concreto de un año
GAS-005: Suma de gastos de un área en una localidad en un año
GAS-006: Suma de gastos de un área en un año dado
GAS-007: Los 10 proveedores con más gastos en un año
GAS-008: Suma de gastos de Montevideo o Mercedes en un año
GAS-009: Suma de gastos del área Jurídica en el año actual
GAS-010: Suma de gastos del área Contable en el año actual
GAS-011: Suma de gastos del área Notarial en el año actual
GAS-012: Suma de gastos del área Recuperación en el año actual
GAS-013: Suma de gastos del área Otros Gastos en el año actual
GAS-014: Suma de gastos del área Administración en el año actual
GAS-015: Suma de gastos en localidad Montevideo en el año actual
GAS-016: Suma de gastos en localidad Mercedes en el año actual
GAS-017: La operación de gasto de mayor monto del año (id, fecha, descripción, proveedor, montos)
GAS-018: Los 5 proveedores con más gastos en el año actual
GAS-019: Los 10 proveedores con más gastos en el año actual
GAS-020: Comparación de gastos entre mes actual y mes anterior
GAS-021: Suma de gastos del trimestre anterior al actual
GAS-022: Evolución mensual de gastos por mes del año actual
GAS-023: Gastos por trimestre del año actual
GAS-024: Gastos por localidad (Montevideo, Mercedes) en el año actual
GAS-025: Gastos desglosados por área en el año actual
GAS-026: Promedio de gastos por mes en el año actual
GAS-027: Total de gastos en USD del año actual
GAS-028: Número de operaciones de gasto en el año actual
GAS-029: Suma de gastos del mes en curso
GAS-030: Suma total de gastos del año en curso
GAS-031: Suma acumulada de todos los gastos (toda la historia)

## RESUMEN
RES-001: Resultado neto UYU y USD (ingresos − gastos) de un año dado
RES-002: Ingresos, gastos, resultado neto, retiros, distribuciones y cantidad de operaciones de un mes concreto
RES-003: El área con mayor porcentaje de rentabilidad en un año (excluye Otros Gastos)
RES-004: Resultado neto UYU por localidad en un año dado
RES-005: Resultado neto (ingresos − gastos) en localidad Montevideo año actual
RES-006: Resultado neto (ingresos − gastos) en localidad Mercedes año actual
RES-007: Resultado neto del área Jurídica en el año actual
RES-008: Resultado neto del área Contable en el año actual
RES-009: Resultado neto del área Notarial en el año actual
RES-010: Ingresos, gastos, resultado, retiros, distribuciones y cantidad del trimestre en curso
RES-011: Área con mayor rentabilidad % en el año actual (excl. Otros Gastos)
RES-012: Área que más ingresos tuvo en el año actual
RES-013: Área que más gastos tuvo en el año actual
RES-014: Localidad con mayor rentabilidad % en el año actual
RES-015: Gastos mensuales de los últimos 12 meses
RES-016: Resultado neto mensual de los últimos 12 meses
RES-017: Cantidad de operaciones por tipo (INGRESO, GASTO, RETIRO, DISTRIBUCION) en el año actual
RES-018: Ingresos por área y porcentaje sobre el total del año actual
RES-019: Gastos por área y porcentaje sobre el total del año actual
RES-020: Ingresos, gastos y resultado en UYU y USD del año actual
RES-021: Resultado neto UYU y USD (ingresos − gastos) del año en curso
RES-022: Resultado neto UYU y USD del mes en curso
RES-023: Evolución mensual del resultado neto en el año actual
RES-024: Resultado neto por área en el año actual
RES-025: Resultado neto por localidad en el año actual
RES-026: Ingresos, gastos, resultado neto, retiros, distribuciones y cantidad de operaciones del año
RES-027: Ingresos, gastos, resultado, retiros, distribuciones y cantidad del mes en curso

## RETIROS
RET-001: Suma de retiros UYU y USD de Montevideo o Mercedes en un año
RET-002: Suma de retiros UYU y USD de un mes concreto o de todo un año
RET-003: Evolución mensual de retiros UYU y USD en un año dado
RET-004: Suma de retiros UYU y USD en Montevideo en el año actual
RET-005: Suma de retiros UYU y USD en Mercedes en el año actual
RET-006: Suma de retiros con moneda original UYU en el año actual
RET-007: Suma de retiros con moneda original USD en el año actual
RET-008: La operación de retiro de mayor monto del año (fecha, descripción, localidad, moneda, montos)
RET-009: Suma de retiros UYU y USD del trimestre anterior al actual
RET-010: Evolución mensual de retiros en el año actual
RET-011: Retiros UYU y USD por trimestre del año actual
RET-012: Retiros UYU y USD por localidad en el año actual
RET-013: Retiros UYU y USD por moneda original (UYU vs USD) en el año actual
RET-014: Promedio de retiros UYU y USD por mes en el año actual
RET-015: Número de operaciones de retiro en el año actual
RET-016: Total de retiros en USD del año actual
RET-017: Suma de retiros UYU y USD del mes en curso
RET-018: Suma total de retiros UYU y USD del año en curso
RET-019: Suma acumulada de todos los retiros (toda la historia)

## DISTRIBUCIONES
DIS-001: Total UYU, USD y cantidad de distribuciones recibidas por un socio en un año
DIS-002: Total UYU y USD de distribuciones de un mes concreto o de todo un año
DIS-003: Totales UYU, USD y cantidad por cada socio en un año dado
DIS-004: Total UYU, USD y cantidad de distribuciones de Bruno en el año actual
DIS-005: Total UYU, USD y cantidad de distribuciones de Agustina en el año actual
DIS-006: Total UYU, USD y cantidad de distribuciones de Viviana en el año actual
DIS-007: Total UYU, USD y cantidad de distribuciones de Gonzalo en el año actual
DIS-008: Total UYU, USD y cantidad de distribuciones de Pancho en el año actual
DIS-009: Totales UYU, USD y cantidad por cada socio en el año actual
DIS-010: Porcentaje real de participación de cada socio en las distribuciones del año
DIS-011: La operación de distribución de mayor monto del año
DIS-012: Total de distribuciones en dólares del año actual
DIS-013: Promedio mensual de distribuciones UYU y USD en el año actual
DIS-014: Número de operaciones de distribución en el año actual
DIS-015: Evolución mensual de distribuciones en el año actual
DIS-016: Distribuciones UYU y USD por trimestre del año actual
DIS-017: Suma de distribuciones UYU y USD del mes en curso
DIS-018: Suma total de distribuciones UYU y USD del año en curso
DIS-019: Suma acumulada de todas las distribuciones (toda la historia)

## COMPUESTAS
COM-001: Ingresos, gastos, resultado y rentabilidad % del mismo mes en dos años (ej. enero 2024 vs enero 2025)
COM-002: Ingresos, gastos, resultado y rentabilidad % de dos meses de un mismo año
COM-003: Ingresos, gastos, resultado y rentabilidad % de un trimestre (Q1-Q4) en dos años
COM-004: Ingresos, gastos y resultado por trimestre (Q1-Q4) de dos años
COM-005: Ingresos, gastos y resultado por semestre (S1, S2) de dos años
COM-006: Ingresos, gastos, resultado y rentabilidad % de dos años
COM-007: Ingresos, gastos, resultado y rentabilidad % de tres años
COM-008: Ingresos, gastos, resultado y rentabilidad % de dos áreas (ej. Jurídica vs Contable)
COM-009: Ingresos, gastos, resultado y rentabilidad % de todas las áreas (año actual, excl. Otros Gastos)
COM-010: Ingresos, gastos, resultado y rentabilidad % de un área en un año
COM-011: Ingresos, gastos, resultado y rentabilidad % de cada área en un año (excl. Otros Gastos)
COM-012: Ingresos, gastos, resultado neto y rentabilidad % global (incluye todos los gastos) en un año
COM-013: Ingresos, gastos y resultado por cada mes de un año
COM-014: Ingresos, gastos, resultado neto, distribuciones, retiros y cantidad de operaciones de un año
COM-015: Comparación de un año con el año anterior (ingresos, gastos, resultado, rentabilidad)
COM-016: Informe ejecutivo: totales, por área, localidad, mes, retiros por localidad/moneda, distribuciones por socio, rentabilidad, top 10 clientes y proveedores
COM-017: Comparación ejecutiva: mismas dimensiones que informe ejecutivo para dos años
COM-018: Rentabilidad % por área en el mes en curso (excl. Otros Gastos)
COM-019: Rentabilidad % por localidad en el mes en curso
COM-020: Rentabilidad % global del mes en curso
COM-021: Ingresos y gastos por localidad en el mes en curso
COM-022: Ingresos, gastos y resultado del mes en curso
COM-023: Número total de operaciones del mes en curso
COM-024: Capital = ingresos − gastos − retiros − distribuciones (acumulado histórico)
COM-025: Entradas, salidas y flujo neto del mes en curso (incluye retiros y distribuciones en salidas)
COM-026: Ingresos, gastos y resultado neto por mes de los últimos 11 meses
COM-027: Total pesificado, componente UYU, USD y cantidad de retiros en Mercedes año actual
COM-028: Total pesificado, componente UYU, USD y cantidad de retiros en Montevideo año actual
