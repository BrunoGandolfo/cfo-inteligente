# Registrar Gasto

## Resumen rápido
Registrar un gasto significa cargar en el sistema dinero que sale del estudio: pagos a proveedores, servicios, alquileres, materiales.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ✅ Sí |

## ¿Dónde está en la pantalla?

### Para socios:
- **Ubicación**: Dashboard → Sección "Registrar Operación" → Segunda card (roja)
- **Botón**: "Registrar Gasto" con ícono de flecha hacia abajo
- **Color**: Borde rojo, ícono rojo
- **Atajo de teclado**: ⌘ + 2

### Para colaboradores:
- **Ubicación**: Pantalla principal → Card derecha
- **Botón**: "Registrar Gasto" con ícono de flecha hacia abajo
- **Color**: Borde rojo al pasar el mouse

---

## Paso a paso detallado

### Para registrar un gasto:

1. **Hacé clic en "Registrar Gasto"**
   - Se abre un modal (ventana emergente) con fondo oscuro atrás
   - Título del modal: "Registrar Gasto"
   - Borde superior: rojo

2. **Completá el campo "Fecha"**
   - Por defecto: fecha de hoy
   - Formato: calendario desplegable
   - **Restricción**: No puede ser fecha futura

3. **Seleccioná el "Área"**
   - Desplegable con todas las áreas del estudio
   - Opciones: Jurídica, Notarial, Contable, Recuperación, Administración, **Otros Gastos**
   - **Obligatorio**: Sí
   - **Nota**: "Otros Gastos" SÍ está disponible para gastos

4. **Seleccioná la "Localidad"**
   - Desplegable con dos opciones
   - Opciones: MVD (Montevideo) o Mercedes
   - Por defecto: Montevideo

5. **Escribí el nombre del "Proveedor"**
   - Campo de texto libre
   - Placeholder: "Nombre del proveedor"
   - **Obligatorio**: Sí
   - Ejemplo: "UTE", "OSE", "Alquiler Local"

6. **Seleccioná la "Moneda"**
   - Desplegable con dos opciones
   - Opciones: UYU (pesos) o USD (dólares)
   - Por defecto: UYU

7. **Ingresá el "Monto"**
   - Campo numérico
   - Placeholder: "0.00"
   - Acepta decimales (con punto: 1500.50)
   - **Obligatorio**: Sí
   - **Validación**: Debe ser mayor a 0

8. **Verificá el "Tipo de Cambio" (T.C.)**
   - Se carga automáticamente desde BCU
   - Podés modificarlo si es necesario
   - Formato: número decimal (ej: 40.50)

9. **Opcionalmente, escribí una "Descripción"**
   - Campo de texto libre
   - Placeholder: "Opcional"
   - Ejemplo: "Factura luz diciembre 2025"

10. **Hacé clic en "Guardar"**
    - Botón verde a la derecha
    - El modal se cierra automáticamente
    - Aparece mensaje verde: "✅ Gasto registrado correctamente"

---

## Campos del formulario

| Campo | Ubicación | Obligatorio | Tipo | Valor por defecto | Validaciones |
|-------|-----------|-------------|------|-------------------|--------------|
| Fecha | Fila 1, izquierda | ✅ | Calendario | Hoy | No futura |
| Área | Fila 1, centro | ✅ | Desplegable | Vacío | Debe seleccionar |
| Local | Fila 1, derecha | ❌ | Desplegable | Montevideo | - |
| Proveedor | Fila 2 completa | ✅ | Texto | Vacío | No vacío |
| Moneda | Fila 3, izquierda | ❌ | Desplegable | UYU | - |
| Monto | Fila 3, centro | ✅ | Número | Vacío | > 0 |
| T.C. | Fila 3, derecha | ✅ | Número | Auto BCU | > 0 |
| Descripción | Fila 4 completa | ❌ | Texto área | Vacío | - |

---

## Opciones de área para gastos

| Área | Descripción | Ejemplos |
|------|-------------|----------|
| Jurídica | Gastos del área jurídica | Tasas judiciales, peritos |
| Notarial | Gastos del área notarial | Timbres, certificados |
| Contable | Gastos del área contable | Software contable, suscripciones |
| Recuperación | Gastos de cobranza | Diligencieros, notificaciones |
| Administración | Gastos administrativos | Papelería, café, limpieza |
| **Otros Gastos** | Gastos operativos generales | Alquiler, luz, agua, internet |

**Nota**: "Otros Gastos" es exclusivo para gastos que no corresponden a un área específica.

---

## Ejemplos concretos

### Ejemplo 1: Pago de alquiler
**Situación**: Pagaste el alquiler de la oficina de Montevideo por $45.000

**Datos a ingresar:**
- Fecha: (fecha del pago)
- Área: **Otros Gastos**
- Local: MVD
- Proveedor: Inmobiliaria XYZ
- Moneda: UYU
- Monto: 45000
- T.C.: (automático)
- Descripción: Alquiler oficina enero 2026

**Resultado**: Se registra gasto de $45.000 en Otros Gastos

### Ejemplo 2: Pago de servicios profesionales en USD
**Situación**: Pagaste USD 200 a un consultor externo

**Datos a ingresar:**
- Fecha: (fecha del pago)
- Área: Contable
- Local: MVD
- Proveedor: Consultor Juan García
- Moneda: USD
- Monto: 200
- T.C.: 42.50 (ejemplo)
- Descripción: Asesoría impositiva

**Resultado**: Se registra gasto por USD 200 (~$8.500 UYU)

### Ejemplo 3: Gasto de la oficina de Mercedes
**Situación**: Se pagó $3.500 de luz de la oficina de Mercedes

**Datos a ingresar:**
- Fecha: (fecha del pago)
- Área: Otros Gastos
- Local: Mercedes
- Proveedor: UTE
- Moneda: UYU
- Monto: 3500
- Descripción: Factura luz diciembre

**Resultado**: Se registra gasto en localidad Mercedes

### Ejemplo 4: Tasa judicial de un expediente
**Situación**: Pagaste $1.200 de tasa judicial para un cliente

**Datos a ingresar:**
- Fecha: (fecha del pago)
- Área: Jurídica
- Local: MVD
- Proveedor: Poder Judicial
- Moneda: UYU
- Monto: 1200
- Descripción: Tasa judicial expediente 123/2026

**Resultado**: Se registra gasto asignado al área Jurídica

---

## Diferencia entre Gasto e Ingreso

| Aspecto | Ingreso | Gasto |
|---------|---------|-------|
| Tipo de operación | Dinero que entra | Dinero que sale |
| Campo principal | Cliente | Proveedor |
| Áreas disponibles | Todas menos "Otros Gastos" | Todas incluyendo "Otros Gastos" |
| Color del botón | Verde | Rojo |

---

## Explicación alternativa

Pensá en el gasto como un pago que hiciste:

1. **¿Cuándo pagaste?** → Fecha
2. **¿A qué área corresponde?** → Área
3. **¿En qué oficina?** → Localidad
4. **¿A quién le pagaste?** → Proveedor
5. **¿En qué moneda?** → Moneda
6. **¿Cuánto?** → Monto
7. **¿A qué cotización?** → Tipo de cambio
8. **¿Por qué concepto?** → Descripción

---

## Errores frecuentes y soluciones

### Error: "Campo obligatorio" en Área
**Por qué aparece:** No seleccionaste un área
**Solución:** Hacé clic en el desplegable de Área y elegí una opción

### Error: "Campo obligatorio" en Proveedor
**Por qué aparece:** El campo proveedor está vacío
**Solución:** Escribí el nombre del proveedor al que le pagaste

### Error: "Campo obligatorio" en Monto
**Por qué aparece:** No ingresaste el monto
**Solución:** Escribí el valor numérico del pago

### Error: No sé qué área usar
**Por qué aparece:** El gasto no corresponde claramente a un área
**Solución:** Usá "Otros Gastos" para gastos generales (alquiler, servicios, etc.)

---

## Preguntas frecuentes

### ¿Cuándo uso "Otros Gastos"?
Usá "Otros Gastos" para:
- Alquiler de oficinas
- Servicios (luz, agua, internet, teléfono)
- Limpieza
- Mantenimiento general
- Gastos que benefician a todo el estudio

### ¿Puedo editar un gasto después de guardarlo?
Sí. Desde el panel de Operaciones, buscá el gasto y hacé clic en "Editar".

### ¿Qué pasa si me equivoco de área?
Podés editarlo después desde el panel de Operaciones.

### ¿Los gastos afectan la rentabilidad?
Sí. A mayor gasto, menor rentabilidad. La fórmula es: Rentabilidad = (Ingresos - Gastos) / Ingresos

---

## Restricciones y limitaciones

- ❌ No se puede registrar fecha futura
- ❌ El monto debe ser mayor a cero
- ❌ El proveedor es obligatorio

---

## Tips y recomendaciones

- 💡 Registrá los gastos el mismo día que se pagan
- 💡 Usá "Otros Gastos" solo para gastos generales, no para gastos de áreas específicas
- 💡 Guardá las facturas para referencia
- 💡 En descripción, incluí el número de factura si lo tenés
- 💡 Si un gasto es compartido entre oficinas, elegí la que más lo usa o dividilo
