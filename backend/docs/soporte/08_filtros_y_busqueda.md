# Filtros y Búsqueda

## Resumen rápido
Los filtros permiten ver solo las operaciones y métricas de un período, localidad o moneda específica.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ❌ No ven filtros |

## ¿Dónde están los filtros?

### En pantallas grandes (2XL+):
- **Ubicación**: Header central, junto a la fecha/hora
- **Visibilidad**: Siempre visibles inline

### En pantallas medianas y pequeñas:
- **Ubicación**: Botón "Filtros" en el header
- **Acción**: Abre un drawer (panel deslizante desde arriba)

---

## Filtros disponibles

### 1. Filtro de Moneda

| Opción | Descripción |
|--------|-------------|
| UYU | Muestra valores en Pesos Uruguayos |
| USD | Muestra valores convertidos a Dólares |

**Comportamiento**:
- Cambia cómo se muestran los montos en las métricas
- No filtra operaciones, solo cambia la visualización
- Usa el tipo de cambio de cada operación para convertir

**Cómo usarlo**:
1. Buscá el toggle UYU/USD
2. Hacé clic para cambiar

### 2. Filtro de Fecha

| Campo | Descripción | Valor por defecto |
|-------|-------------|-------------------|
| Desde | Fecha inicial del período | Primer día del mes |
| Hasta | Fecha final del período | Hoy |

**Comportamiento**:
- Filtra operaciones que estén dentro del rango
- Afecta métricas, gráficos y panel de operaciones
- Formato: calendario desplegable

**Cómo usarlo**:
1. Hacé clic en el campo "Desde"
2. Seleccioná la fecha inicial
3. Hacé clic en el campo "Hasta"
4. Seleccioná la fecha final
5. Los filtros se aplican automáticamente

### 3. Filtro de Localidad

| Opción | Descripción |
|--------|-------------|
| Todas | Muestra todas las localidades |
| Montevideo | Solo operaciones de Montevideo |
| Mercedes | Solo operaciones de Mercedes |

**Comportamiento**:
- Filtra operaciones por la localidad seleccionada
- Afecta métricas, gráficos y panel de operaciones

**Cómo usarlo**:
1. Buscá el desplegable de localidad
2. Seleccioná la opción deseada

---

## Filtros activos

Cuando tenés filtros aplicados, aparece una barra debajo de las métricas:

```
Filtros activos: [01/12 - 15/12 ×] [Mercedes ×] [USD]
```

### Elementos:

| Badge | Color | Acción del ×|
|-------|-------|-------------|
| Rango de fechas | Azul | Resetea al mes actual |
| Localidad | Púrpura | Cambia a "Todas" |
| Moneda | Verde | Solo informativo, sin × |

**Cómo quitar un filtro**:
- Hacé clic en la × del badge correspondiente
- O cambiá el valor en los controles del header

---

## Drawer de filtros (pantallas pequeñas)

En pantallas menores a 2XL, los filtros están en un drawer:

### Cómo abrirlo:
1. En el header, buscá el botón "Filtros" (con ícono de embudo)
2. Si hay filtros activos, muestra un número (badge azul)
3. Hacé clic para abrir el drawer

### Contenido del drawer:
- Selector de moneda (UYU/USD)
- Selector de fecha desde
- Selector de fecha hasta
- Selector de localidad
- Botón "Limpiar filtros"
- Botón "Cerrar"

### Cómo cerrarlo:
- Hacé clic en "Cerrar"
- O hacé clic fuera del drawer

---

## Ejemplos concretos

### Ejemplo 1: Ver solo operaciones de diciembre 2025
1. Abrí los filtros
2. En "Desde": 01/12/2025
3. En "Hasta": 31/12/2025
4. Las métricas y gráficos muestran solo diciembre

### Ejemplo 2: Comparar Montevideo vs Mercedes
1. Primero: Poné localidad "Montevideo"
2. Anotá los valores de ingresos/gastos
3. Después: Cambiá a "Mercedes"
4. Compará los valores

### Ejemplo 3: Ver cuánto se facturó en USD
1. Cambiá moneda a "USD"
2. Mirá las métricas
3. Los valores muestran equivalentes en dólares

### Ejemplo 4: Ver el año completo
1. En "Desde": 01/01/2026
2. En "Hasta": 31/12/2026
3. Ves las métricas anuales

---

## Cómo se aplican los filtros

| Filtro | Afecta métricas | Afecta gráficos | Afecta operaciones |
|--------|-----------------|-----------------|-------------------|
| Moneda | ✅ Vista | ✅ Vista | ❌ No |
| Fecha | ✅ Filtra | ✅ Filtra | ✅ Filtra |
| Localidad | ✅ Filtra | ✅ Filtra | ✅ Filtra |

---

## Valores por defecto

Cuando entrás al sistema o limpiás filtros:

| Filtro | Valor por defecto |
|--------|-------------------|
| Moneda | UYU |
| Desde | Primer día del mes actual |
| Hasta | Hoy |
| Localidad | Todas |

---

## Errores frecuentes y soluciones

### Error: Las métricas muestran $0
**Por qué aparece:** No hay operaciones en el período filtrado
**Solución:** Ampliá el rango de fechas

### Error: No veo operaciones que sé que cargué
**Por qué aparece:** La operación está fuera del rango de fechas
**Solución:** Verificá y ajustá las fechas del filtro

### Error: Los números parecen raros
**Por qué aparece:** Puede que estés viendo en USD en lugar de UYU
**Solución:** Verificá el toggle de moneda

### Error: "No hay operaciones en el período seleccionado"
**Por qué aparece:** El rango de fechas o localidad excluyen todas las operaciones
**Solución:** 
- Hacé clic en "Limpiar filtros" si está disponible
- O ajustá manualmente fecha/localidad

---

## Preguntas frecuentes

### ¿Los filtros se guardan al cerrar sesión?
No. Cada vez que entrás, los filtros vuelven a los valores por defecto.

### ¿Puedo guardar filtros favoritos?
No. Esta funcionalidad no está disponible actualmente.

### ¿Por qué no veo el botón de filtros?
Puede ser que:
- Sos colaborador (no ven filtros)
- Estás en pantalla grande y los filtros están inline en el header

### ¿Los filtros afectan a otros usuarios?
No. Cada usuario tiene sus propios filtros independientes.

---

## Restricciones y limitaciones

- ❌ Los colaboradores no tienen acceso a filtros
- ❌ No se pueden guardar combinaciones de filtros
- ❌ No hay filtro por tipo de operación
- ❌ No hay filtro por área
- ❌ No hay búsqueda por texto

---

## Tips y recomendaciones

- 💡 Usá fechas del mismo período para comparar (ej: enero vs enero)
- 💡 Verificá los filtros si los números te parecen raros
- 💡 Limpiá filtros antes de empezar un análisis nuevo
- 💡 El filtro de moneda cambia la vista, no el dato real
- 💡 Para ver todo el año, poné desde 01/01 hasta 31/12
