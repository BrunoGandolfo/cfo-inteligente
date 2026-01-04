# Registrar Ingreso

## Resumen rápido
Registrar un ingreso significa cargar en el sistema dinero que entra al estudio: cobros a clientes, honorarios, ventas de servicios.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ✅ Sí |

## ¿Dónde está en la pantalla?

### Para socios:
- **Ubicación**: Dashboard → Sección "Registrar Operación" → Primera card (verde)
- **Botón**: "Registrar Ingreso" con ícono de flecha hacia arriba
- **Color**: Borde verde, ícono verde
- **Atajo de teclado**: ⌘ + 1

### Para colaboradores:
- **Ubicación**: Pantalla principal → Card izquierda
- **Botón**: "Registrar Ingreso" con ícono de flecha hacia arriba
- **Color**: Borde verde al pasar el mouse

---

## Paso a paso detallado

### Para registrar un ingreso:

1. **Hacé clic en "Registrar Ingreso"**
   - Se abre un modal (ventana emergente) con fondo oscuro atrás
   - Título del modal: "Registrar Ingreso"
   - Borde superior: verde (emerald)

2. **Completá el campo "Fecha"**
   - Por defecto: fecha de hoy
   - Formato: calendario desplegable
   - **Restricción**: No puede ser fecha futura

3. **Seleccioná el "Área"**
   - Desplegable con las áreas del estudio
   - Opciones: Jurídica, Notarial, Contable, Recuperación, Administración
   - **Nota**: "Otros Gastos" NO aparece para ingresos
   - **Obligatorio**: Sí

4. **Seleccioná la "Localidad"**
   - Desplegable con dos opciones
   - Opciones: MVD (Montevideo) o Mercedes
   - Por defecto: Montevideo

5. **Escribí el nombre del "Cliente"**
   - Campo de texto libre
   - Placeholder: "Nombre del cliente"
   - **Obligatorio**: Sí
   - Ejemplo: "Empresa ABC S.A."

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
   - Ejemplo: "Honorarios por asesoría legal contrato XYZ"

10. **Hacé clic en "Guardar"**
    - Botón verde a la derecha
    - El modal se cierra automáticamente
    - Aparece mensaje verde: "✅ Ingreso registrado correctamente"

---

## Campos del formulario

| Campo | Ubicación | Obligatorio | Tipo | Valor por defecto | Validaciones |
|-------|-----------|-------------|------|-------------------|--------------|
| Fecha | Fila 1, izquierda | ✅ | Calendario | Hoy | No futura |
| Área | Fila 1, centro | ✅ | Desplegable | Vacío | Debe seleccionar |
| Local | Fila 1, derecha | ❌ | Desplegable | Montevideo | - |
| Cliente | Fila 2 completa | ✅ | Texto | Vacío | No vacío |
| Moneda | Fila 3, izquierda | ❌ | Desplegable | UYU | - |
| Monto | Fila 3, centro | ✅ | Número | Vacío | > 0 |
| T.C. | Fila 3, derecha | ✅ | Número | Auto BCU | > 0 |
| Descripción | Fila 4 completa | ❌ | Texto área | Vacío | - |

---

## Opciones de área para ingresos

| Área | Descripción |
|------|-------------|
| Jurídica | Cobros por servicios legales |
| Notarial | Cobros por servicios notariales |
| Contable | Cobros por servicios contables |
| Recuperación | Cobros por gestión de cobranzas |
| Administración | Cobros por servicios administrativos |

**Nota**: "Otros Gastos" NO está disponible para ingresos.

---

## Ejemplos concretos

### Ejemplo 1: Cobro de honorarios en pesos
**Situación**: Cobraste $50.000 a un cliente por servicios jurídicos en Montevideo

**Datos a ingresar:**
- Fecha: (hoy, o la fecha del cobro)
- Área: Jurídica
- Local: MVD
- Cliente: Cliente ABC S.A.
- Moneda: UYU
- Monto: 50000
- T.C.: (automático)
- Descripción: Honorarios asesoría contractual

**Resultado**: Se registra ingreso por $50.000 UYU

### Ejemplo 2: Cobro en dólares
**Situación**: Cobraste USD 500 a un cliente extranjero por servicios contables

**Datos a ingresar:**
- Fecha: (fecha del cobro)
- Área: Contable
- Local: MVD
- Cliente: International Corp
- Moneda: USD
- Monto: 500
- T.C.: 42.50 (ejemplo)
- Descripción: Consultoría tributaria

**Resultado**: Se registra ingreso por USD 500 (equivalente a ~$21.250 UYU)

### Ejemplo 3: Cobro en Mercedes
**Situación**: Se cobró $15.000 por servicios notariales en la oficina de Mercedes

**Datos a ingresar:**
- Fecha: (fecha del cobro)
- Área: Notarial
- Local: Mercedes
- Cliente: Juan Pérez
- Moneda: UYU
- Monto: 15000
- Descripción: Escritura compraventa

**Resultado**: Se registra ingreso en localidad Mercedes

---

## Explicación alternativa

Imaginá que el ingreso es como una factura que cobraste:

1. **¿Cuándo cobraste?** → Fecha
2. **¿De qué área es el servicio?** → Área
3. **¿En qué oficina?** → Localidad
4. **¿Quién te pagó?** → Cliente
5. **¿En qué moneda?** → Moneda
6. **¿Cuánto?** → Monto
7. **¿A qué cotización?** → Tipo de cambio
8. **¿Qué servicio prestaste?** → Descripción

---

## Errores frecuentes y soluciones

### Error: "Campo obligatorio" en Área
**Por qué aparece:** No seleccionaste un área
**Solución:** Hacé clic en el desplegable de Área y elegí una opción

### Error: "Campo obligatorio" en Cliente
**Por qué aparece:** El campo cliente está vacío
**Solución:** Escribí el nombre del cliente que pagó

### Error: "Campo obligatorio" en Monto
**Por qué aparece:** No ingresaste el monto
**Solución:** Escribí el valor numérico del cobro

### Error: El tipo de cambio muestra 40.50 incorrecto
**Por qué aparece:** No se pudo obtener el TC del BCU
**Solución:** Modificá manualmente el tipo de cambio al valor correcto

### Error: No puedo seleccionar fecha futura
**Por qué aparece:** El sistema solo permite fechas pasadas o de hoy
**Solución:** No se pueden registrar cobros futuros, esperá a que ocurra el cobro

---

## Preguntas frecuentes

### ¿Puedo editar un ingreso después de guardarlo?
Sí. Desde el panel de Operaciones, buscá el ingreso y hacé clic en "Editar".

### ¿Puedo eliminar un ingreso mal cargado?
Sí. Desde el panel de Operaciones, buscá el ingreso y hacé clic en "Eliminar".

### ¿Qué pasa si pongo mal el cliente?
Podés editarlo después desde el panel de Operaciones.

### ¿El tipo de cambio se guarda aunque ponga UYU?
Sí, el TC se guarda siempre para poder mostrar equivalencias.

### ¿Puedo cargar varios ingresos seguidos?
Sí, después de guardar uno, podés abrir el modal nuevamente y cargar otro.

---

## Restricciones y limitaciones

- ❌ No se puede registrar fecha futura
- ❌ No se puede usar "Otros Gastos" como área
- ❌ El monto debe ser mayor a cero
- ❌ El cliente es obligatorio

---

## Tips y recomendaciones

- 💡 Registrá los ingresos el mismo día que se producen
- 💡 Usá descripciones claras para identificar el servicio
- 💡 Verificá el tipo de cambio si cobrás en dólares
- 💡 Si un cliente paga en partes, registrá cada pago como ingreso separado
- 💡 El área debe coincidir con el tipo de servicio prestado
