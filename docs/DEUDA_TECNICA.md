# Deuda Técnica - CFO Inteligente

**Última actualización:** 2024-12-19
**Estado del código:** Post-refactorización P0

---

## Resumen Ejecutivo

| Categoría | Completado | Pendiente |
|-----------|------------|-----------|
| Limpieza de código | ✅ P0 | - |
| Complejidad crítica | ✅ 1/9 | 8 funciones D |
| Cobertura crítica | ✅ 2/5 | 3 archivos <70% |
| Archivos grandes | ❌ | 10 archivos >300 líneas |

---

## P0 - COMPLETADO ✅

| Item | Estado | Descripción |
|------|--------|-------------|
| Imports sin usar | ✅ | 0 (autoflake ejecutado) |
| Variables sin usar | ✅ | 0 (F841 limpio) |
| Prints de debug | ✅ | 0 (convertidos a logger) |
| `actualizar_operacion` | ✅ | E(31) → A(1) |
| Filtros duplicados | ✅ | Extraído a `query_helpers.py` |
| Prompts duplicados | ✅ | Extraído a `prompts.py` |
| Checkpoint | ✅ | Tag `v1.0-pre-refactor` |

---

## P1 - ALTA PRIORIDAD (Pendiente)

### Funciones con Complejidad D (>20)

| # | Función | Complejidad | Archivo | Líneas | Acción Requerida |
|---|---------|-------------|---------|--------|------------------|
| 1 | `resumen_mensual` | D (27) | `app/api/reportes.py:25` | ~40 | Extraer calculators |
| 2 | `detectar_tipo_query` | D (26) | `app/services/validador_sql.py:40` | ~50 | Dict de patterns |
| 3 | `validar_sql_antes_ejecutar` | D (25) | `app/services/validador_sql.py:348` | ~100 | Dividir en 4 métodos |
| 4 | `_generate_charts` | D (24) | `app/services/report_orchestrator.py:382` | ~200 | Strategy pattern |
| 5 | `QueryFallback.get_query_for` | D (23) | `app/services/query_fallback.py:15` | ~100 | Mover patterns a JSON |
| 6 | `calculate_main_metrics` | D (22) | `app/services/report_data/base_aggregator.py:175` | ~150 | Dividir en calculators |
| 7 | `dashboard_report` | D (21) | `app/api/reportes_dashboard.py:13` | ~75 | Extraer helpers |
| 8 | `preguntar_cfo` | D (21) | `app/api/cfo_ai.py:76` | ~150 | Ya usa servicios, simplificar |

**Esfuerzo estimado:** ~8 horas

### Cobertura < 70%

| Archivo | Cobertura | Líneas sin cubrir | Prioridad |
|---------|-----------|-------------------|-----------|
| `app/api/operaciones.py` | 32% | 79 líneas | 🔴 Alta |
| `app/api/reportes.py` | 65% | 27 líneas | 🟠 Media |
| `app/api/cfo_ai.py` | 73% | 36 líneas | 🟡 Baja |

**Esfuerzo estimado:** ~4 horas

---

## P2 - MEDIA PRIORIDAD (Backlog)

### Archivos Grandes (>300 líneas) - Potenciales God Objects

| # | Archivo | Líneas | Responsabilidades | Refactorización |
|---|---------|--------|-------------------|-----------------|
| 1 | `report_orchestrator.py` | 693 | Orchestration + Charts + Insights + Cleanup | Dividir en ChartGenerator, InsightGenerator |
| 2 | `sql_router.py` | 595 | Routing + Claude + Vanna + Stats | Extraer VannaAdapter, ClaudeAdapter |
| 3 | `report_builder.py` | 555 | PDF Building completo | Dividir por sección |
| 4 | `validador_sql.py` | 507 | Detección + Pre + Post + Sintaxis | Dividir en PreValidator, PostValidator |
| 5 | `base_aggregator.py` | 494 | Métricas + Histórico + Comparaciones | Extraer a calculators específicos |
| 6 | `validador_canonico.py` | 492 | 20 queries de control | Mover queries a JSON/YAML |
| 7 | `pnl_localidad_generator.py` | 428 | Generación de reporte PNL | Evaluar si se puede modularizar |
| 8 | `claude_sql_generator.py` | 422 | Generación SQL con Claude | Ya está bien encapsulado |
| 9 | `metrics_aggregator.py` | 400 | Agregación de métricas | Usar composición |
| 10 | `endpoints/reports.py` | 380 | Múltiples endpoints de reportes | Dividir por tipo de reporte |

**Esfuerzo estimado:** ~16 horas

### TODOs Pendientes en Código

| Ubicación | TODO | Prioridad |
|-----------|------|-----------|
| `aggregator_factory.py:31` | Implementar WeeklyAggregator | 🟡 Baja |
| `aggregator_factory.py:32` | Implementar QuarterlyAggregator | 🟡 Baja |
| `aggregator_factory.py:33` | Implementar YearlyAggregator | 🟡 Baja |
| `tipo_cambio_service.py:77` | Implementar BCU SOAP | 🟡 Baja |

---

## P3 - BAJA PRIORIDAD (Mejoras Futuras)

### Mejoras de Testing

| Item | Estado Actual | Objetivo |
|------|---------------|----------|
| Tests de integración | 9 errors por setup BD | Arreglar fixtures |
| Tests de mocks Claude | 15 fallos | Actualizar mocks |
| Cobertura global | 72% | 80%+ |

### Mejoras de Arquitectura

| Item | Descripción |
|------|-------------|
| Interfaces/ABC | Solo 5 clases abstractas, agregar más |
| Inyección de dependencias | API importa 29 servicios directamente |
| Documentación inline | Agregar docstrings faltantes |

---

## Cronograma Sugerido

| Sprint | Items | Esfuerzo |
|--------|-------|----------|
| Sprint 1 | P1 funciones críticas (1-4) | 4h |
| Sprint 2 | P1 cobertura operaciones.py | 2h |
| Sprint 3 | P1 funciones restantes (5-8) | 4h |
| Sprint 4 | P2 archivos grandes (1-2) | 8h |
| Backlog | P2 restante + P3 | ~12h |

**Total estimado:** ~30 horas

---

## Notas

- La app **funciona correctamente** en producción
- Los tests críticos (569) pasan
- La cobertura en archivos más usados (cfo_streaming, operacion_service) es >95%
- Esta deuda técnica es **técnica, no funcional** - no hay bugs conocidos

---

## Historial

| Fecha | Cambio |
|-------|--------|
| 2024-12-19 | Documento creado post-refactorización P0 |

