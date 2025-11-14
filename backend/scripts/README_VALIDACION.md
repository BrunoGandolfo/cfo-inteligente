# 🔍 Sistema de Validación Automática de Queries SQL

Sistema de auditoría y validación de queries SQL generadas por Claude en CFO Inteligente.

---

## 📦 Archivos Incluidos

```
backend/scripts/
├── validador_queries_automatico.py  # Detector automático de patrones problemáticos
├── validar_interactivo.py           # Validación manual interactiva
└── README_VALIDACION.md             # Esta documentación
```

---

## 🚀 Guía de Uso Rápida

### Paso 1: Análisis Automático

```bash
cd backend/scripts
python validador_queries_automatico.py
```

**Genera:**
- `backend/output/queries_sospechosas.json` - Datos estructurados
- `backend/output/queries_sospechosas.md` - Reporte legible

---

### Paso 2: Validación Interactiva (Opcional)

```bash
cd backend/scripts
python validar_interactivo.py
```

**Funcionalidad:**
- Ejecuta SQL original vs corregido
- Compara resultados lado a lado
- Pregunta al usuario cuál es correcto
- Genera reporte final con % de confianza

---

## 🔬 Patrones Detectados

### 🔴 ALTA CRITICIDAD (Error 49-650%)

#### Patrón 1: LEFT JOIN con filtros temporales en ON
```sql
-- ❌ INCORRECTO
FROM socios s
LEFT JOIN distribuciones_detalle dd ON s.id = dd.socio_id
LEFT JOIN operaciones o ON dd.operacion_id = o.id
    AND EXTRACT(YEAR FROM o.fecha) = 2024  -- Filtro en ON

-- ✅ CORRECTO
FROM distribuciones_detalle dd
INNER JOIN operaciones o ON dd.operacion_id = o.id
INNER JOIN socios s ON dd.socio_id = s.id
WHERE EXTRACT(YEAR FROM o.fecha) = 2024  -- Filtro en WHERE
```

**Error causado:** Suma distribuciones de TODOS los años, no solo el filtrado

---

#### Patrón 2: FROM tabla maestra + LEFT JOIN a detalles
```sql
-- ❌ INCORRECTO
FROM socios s
LEFT JOIN distribuciones_detalle dd ON s.id = dd.socio_id

-- ✅ CORRECTO (para agregaciones)
FROM distribuciones_detalle dd
INNER JOIN socios s ON dd.socio_id = s.id
```

---

### 🟡 MEDIA CRITICIDAD

#### Patrón 3: Agregación sin filtro temporal en distribuciones
```sql
-- ⚠️ SOSPECHOSO
SELECT SUM(dd.monto_uyu)
FROM distribuciones_detalle dd
-- Sin WHERE fecha = ... (suma TODO el histórico)
```

---

#### Patrón 4: Múltiples LEFT JOINs anidados (>2)
```sql
-- ⚠️ SOSPECHOSO (complejidad alta)
FROM tabla1
LEFT JOIN tabla2 ON ...
LEFT JOIN tabla3 ON ...
LEFT JOIN tabla4 ON ...
```

---

### 🟢 BAJA CRITICIDAD

#### Patrón 5: COALESCE en SUM con LEFT JOIN
```sql
-- 🟢 REVISAR (puede ser correcto)
SELECT COALESCE(SUM(monto), 0)
FROM tabla1
LEFT JOIN tabla2 ON ...
```

**Nota:** Este patrón es correcto cuando se comparan 2 CTEs independientes.

---

## 📊 Interpretación de Resultados

### Archivo: `queries_sospechosas.json`

```json
{
  "estadisticas": {
    "total_queries": 69,
    "queries_sospechosas": 4,
    "alta_criticidad": 2,
    "media_criticidad": 1,
    "baja_criticidad": 1,
    "porcentaje_correctas": 97.1
  },
  "queries_sospechosas": [
    {
      "id": "uuid...",
      "criticidad": "ALTA",
      "problemas": [...],
      "sql_original": "...",
      "sql_corregido": "..."
    }
  ]
}
```

**Interpretación:**
- `alta_criticidad`: Validar INMEDIATAMENTE
- `media_criticidad`: Validar en 1-2 días
- `baja_criticidad`: Validar cuando sea posible
- `porcentaje_correctas`: Meta >95%

---

### Archivo: `reporte_validacion_final.json`

```json
{
  "confianza_sistema": 97.5,
  "decisiones": {
    "original_correcto": 1,
    "corregido_correcto": 2,
    "ambos_iguales": 0,
    "error_confirmado": 1
  }
}
```

**Interpretación:**
- `confianza_sistema`: % de queries correctas después de validación
- `corregido_correcto`: Queries con error confirmado (requieren fix en prompt)
- `original_correcto`: Falsas alarmas (detector muy sensible)

---

## 🎯 Casos de Uso

### Caso 1: Auditoría Post-Deployment
```bash
# Después de actualizar prompts, validar impacto
python validador_queries_automatico.py
# Verificar que queries_sospechosas disminuyan
```

### Caso 2: Investigar Error Reportado por Usuario
```bash
# Usuario reporta dato incorrecto
# 1. Ejecutar validador automático
python validador_queries_automatico.py

# 2. Buscar query en queries_sospechosas.md
# 3. Ejecutar validador interactivo
python validar_interactivo.py

# 4. Comparar resultados
```

### Caso 3: Validación Periódica (Semanal)
```bash
# Cronjob o tarea programada
0 9 * * 1 cd /path/to/backend/scripts && python validador_queries_automatico.py
# Revisar queries_sospechosas.md cada lunes
```

---

## 🔧 Configuración

### Variables de Entorno

Editar en cada script si es necesario:

```python
# Base de datos
DB_URL = "postgresql://postgres:postgres@localhost:5432/cfo_inteligente"

# Rutas de output
OUTPUT_DIR = Path(__file__).parent.parent / "output"
```

---

## ⚠️ Limitaciones

1. **Validador automático:**
   - Detecta patrones sintácticos, no errores lógicos
   - Puede tener falsos positivos (queries correctas marcadas como sospechosas)
   - No ejecuta queries (solo análisis estático)

2. **Validador interactivo:**
   - Requiere intervención manual
   - Usuario debe interpretar resultados
   - No detecta errores semánticos sutiles

---

## 🧪 Testing

### Test del validador automático:

```bash
python validador_queries_automatico.py

# Verificar outputs:
ls -lh ../output/queries_sospechosas.*
# Debe crear: queries_sospechosas.json y queries_sospechosas.md
```

### Test del validador interactivo:

```bash
python validar_interactivo.py

# Flujo:
# 1. Muestra primera query sospechosa
# 2. Pregunta si ejecutar
# 3. Ejecuta ambas queries
# 4. Muestra resultados
# 5. Pregunta cuál es correcta
# 6. Guarda decisión
# 7. Repite con siguiente query
```

---

## 📈 Métricas de Éxito

| Métrica | Meta | Actual | Estado |
|---------|------|--------|--------|
| **Confiabilidad general** | >95% | 97.1% | ✅ |
| **Queries alta criticidad** | 0 | 2 | ⚠️ |
| **Tiempo detección** | <5 min | ~2 min | ✅ |
| **Falsas alarmas** | <10% | TBD | - |

---

## 🤝 Contribuir

Si encuentras nuevos patrones problemáticos:

1. Agregar detector en `validador_queries_automatico.py`
2. Definir criticidad (ALTA/MEDIA/BAJA)
3. Agregar ejemplo en esta documentación
4. Actualizar REGLAS en `claude_sql_generator.py`

---

## 📞 Soporte

**Reportar problemas:**
- Guardar `queries_sospechosas.json`
- Captura de pantalla de validación interactiva
- SQL original y resultado obtenido

---

**Última actualización:** 2025-11-14  
**Versión:** 1.0.0

