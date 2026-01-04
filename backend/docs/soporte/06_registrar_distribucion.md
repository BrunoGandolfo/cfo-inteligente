# Registrar Distribución

## Resumen rápido
Una distribución es el reparto formal de utilidades entre los 5 socios del estudio. Se registran los montos que recibe cada socio.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ❌ No |

**Importante**: Solo los socios pueden registrar distribuciones. Los colaboradores no ven esta opción.

## ¿Dónde está en la pantalla?

- **Ubicación**: Dashboard → Sección "Registrar Operación" → Cuarta card (azul)
- **Botón**: "Distribución de Utilidades" con ícono de usuarios
- **Color**: Borde azul, ícono azul
- **Atajo de teclado**: ⌘ + 4
- **Nota inferior**: "Se realiza a fin de mes"

---

## ¿Qué es una distribución?

Una distribución es el reparto de utilidades o ganancias entre los 5 socios del estudio:

1. **Agustina** (aborio)
2. **Viviana** (vcaresani)
3. **Gonzalo** (gtaborda)
4. **Pancho** (falgorta)
5. **Bruno** (bgandolfo)

### Diferencia con Retiro:
| Distribución | Retiro |
|--------------|--------|
| Todos los socios | Un solo socio |
| Reparto formal | Extracción individual |
| Típicamente fin de mes | Cuando se necesita |
| Montos para cada uno | Monto único |

---

## Paso a paso detallado

### Para registrar una distribución:

1. **Hacé clic en "Distribución de Utilidades"**
   - Se abre un modal con título "Registrar Distribución"
   - Borde superior: azul

2. **Completá el campo "Fecha"**
   - Por defecto: fecha de hoy
   - **Restricción**: No puede ser fecha futura

3. **Seleccioná la "Localidad"**
   - Desplegable: Montevideo o Mercedes
   - Por defecto: Montevideo

4. **Verificá el "Tipo de Cambio" (T.C.)**
   - Se carga automáticamente desde BCU
   - Se usa para calcular equivalencias

5. **Ingresá los montos para cada socio**:

   | Socio | UYU | USD |
   |-------|-----|-----|
   | Agustina | [monto pesos] | [monto dólares] |
   | Viviana | [monto pesos] | [monto dólares] |
   | Gonzalo | [monto pesos] | [monto dólares] |
   | Pancho | [monto pesos] | [monto dólares] |
   | Bruno | [monto pesos] | [monto dólares] |

6. **Opcionalmente, escribí una "Descripción"**
   - Campo de texto
   - Ejemplo: "Distribución utilidades enero 2026"

7. **Hacé clic en "Guardar"**
   - Mensaje: "✅ Distribución registrada correctamente"

---

## Campos del formulario

### Campos generales:

| Campo | Ubicación | Obligatorio | Tipo | Valor por defecto |
|-------|-----------|-------------|------|-------------------|
| Fecha | Fila 1, izquierda | ✅ | Calendario | Hoy |
| Localidad | Fila 1, centro | ❌ | Desplegable | Montevideo |
| T.C. | Fila 1, derecha | ✅ | Número | Auto BCU |

### Montos por socio (grilla):

| Socio | Campo UYU | Campo USD |
|-------|-----------|-----------|
| Agustina | agustina_uyu | agustina_usd |
| Viviana | viviana_uyu | viviana_usd |
| Gonzalo | gonzalo_uyu | gonzalo_usd |
| Pancho | pancho_uyu | pancho_usd |
| Bruno | bruno_uyu | bruno_usd |

Todos los campos de monto son opcionales. Podés dejar en blanco a socios que no participan de esa distribución.

---

## Ejemplos concretos

### Ejemplo 1: Distribución igualitaria en pesos
**Situación**: Se reparten $500.000 entre los 5 socios en partes iguales

**Datos a ingresar:**
- Fecha: 31/01/2026
- Localidad: Montevideo
- T.C.: (automático)
- Agustina UYU: 100000
- Viviana UYU: 100000
- Gonzalo UYU: 100000
- Pancho UYU: 100000
- Bruno UYU: 100000
- Descripción: Distribución enero - partes iguales

### Ejemplo 2: Distribución con diferentes montos
**Situación**: Se distribuyen utilidades según participación societaria

**Datos a ingresar:**
- Fecha: 31/01/2026
- Localidad: Montevideo
- Agustina UYU: 150000
- Viviana UYU: 120000
- Gonzalo UYU: 100000
- Pancho UYU: 80000
- Bruno UYU: 50000
- Descripción: Distribución enero - según participación

### Ejemplo 3: Distribución mixta (pesos y dólares)
**Situación**: Algunos socios reciben en pesos y otros en dólares

**Datos a ingresar:**
- Fecha: 31/01/2026
- Localidad: Montevideo
- Agustina UYU: 80000
- Agustina USD: 500
- Viviana UYU: 100000
- Gonzalo UYU: 100000
- Pancho USD: 1000
- Bruno UYU: 50000
- Bruno USD: 300
- Descripción: Distribución mixta enero

### Ejemplo 4: Distribución parcial (no todos los socios)
**Situación**: Solo 3 socios participan de esta distribución

**Datos a ingresar:**
- Fecha: 31/01/2026
- Agustina UYU: 50000
- Viviana UYU: 50000
- Bruno UYU: 50000
- (Gonzalo y Pancho sin montos)
- Descripción: Distribución parcial - proyecto especial

---

## Explicación alternativa

Pensalo como un sobre para cada socio con su parte de las ganancias:

1. **¿Cuándo se reparte?** → Fecha
2. **¿De qué caja?** → Localidad
3. **¿Cuánto lleva cada uno?** → Montos por socio
4. **¿Por qué concepto?** → Descripción

Cada socio puede recibir:
- Solo pesos
- Solo dólares
- Ambos
- Nada (si no participa de esa distribución)

---

## Errores frecuentes y soluciones

### Error: "Solo socios pueden registrar distribuciones"
**Por qué aparece:** Intentaste registrar distribución pero tu cuenta es de colaborador
**Solución:** Solo los socios pueden hacer distribuciones. Contactá a un socio.

### Error: Todos los montos vacíos
**Por qué aparece:** No pusiste ningún monto para ningún socio
**Solución:** Completá al menos un monto para al menos un socio

### Error: "No puedo ver el botón de Distribución"
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Los colaboradores no ven esta opción. Es normal.

---

## Preguntas frecuentes

### ¿Puedo hacer varias distribuciones en un mes?
Sí. No hay límite. Podés hacer distribuciones semanales, quincenales o cuando lo decidan.

### ¿Qué pasa si un socio no recibe nada?
Dejá sus campos vacíos. No es obligatorio que todos reciban en cada distribución.

### ¿Las distribuciones afectan las métricas del Dashboard?
Las distribuciones son movimientos de capital, no gastos ni ingresos operativos.

### ¿Puedo editar una distribución?
Sí. Desde el panel de Operaciones podés editar o eliminar distribuciones.

### ¿Por qué hay campos separados para UYU y USD?
Porque un socio puede querer recibir parte en pesos y parte en dólares, o diferentes socios pueden preferir diferentes monedas.

---

## Restricciones y limitaciones

- ❌ Solo socios pueden registrar distribuciones
- ❌ No puede ser fecha futura
- ❌ Debe tener al menos un monto para al menos un socio
- ❌ No se puede cambiar la lista de socios (son los 5 fijos)

---

## Tips y recomendaciones

- 💡 Registrá las distribuciones al final de cada mes
- 💡 Usá descripción para identificar el período (ej: "Enero 2026")
- 💡 Si un socio no participa, dejá sus campos vacíos
- 💡 Verificá el tipo de cambio antes de guardar si hay montos en USD
- 💡 Coordiná con los demás socios antes de registrar la distribución
