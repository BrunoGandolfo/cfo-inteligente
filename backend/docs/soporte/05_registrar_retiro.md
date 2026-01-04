# Registrar Retiro

## Resumen rápido
Un retiro es cuando un socio saca dinero del estudio para su uso personal. Es diferente a una distribución porque el retiro es individual.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ❌ No |

**Importante**: Solo los socios pueden registrar retiros. Los colaboradores no ven esta opción.

## ¿Dónde está en la pantalla?

- **Ubicación**: Dashboard → Sección "Registrar Operación" → Tercera card (ámbar)
- **Botón**: "Retiro de Empresa" con ícono de billetera
- **Color**: Borde ámbar/naranja, ícono ámbar
- **Atajo de teclado**: ⌘ + 3
- **Nota inferior**: "Se realiza a fin de mes"

---

## ¿Qué es un retiro?

Un retiro es dinero que un socio extrae del estudio para sí mismo. Características:

- Es **individual**: un socio retira para sí mismo
- No se asigna a un área
- Puede ser en pesos (UYU) o dólares (USD) o ambos
- No tiene cliente ni proveedor asociado
- Afecta el flujo de caja del estudio

### Diferencia con Distribución:
| Retiro | Distribución |
|--------|--------------|
| Un solo socio | Todos los socios |
| Monto libre | Montos para cada socio |
| Cuando necesita | Típicamente fin de mes |
| No está estandarizado | Reparto formal de utilidades |

---

## Paso a paso detallado

### Para registrar un retiro:

1. **Hacé clic en "Retiro de Empresa"**
   - Se abre un modal con título "Registrar Retiro"
   - Borde superior: ámbar/naranja

2. **Completá el campo "Fecha"**
   - Por defecto: fecha de hoy
   - **Restricción**: No puede ser fecha futura

3. **Seleccioná la "Localidad"**
   - Desplegable: Montevideo o Mercedes
   - Por defecto: Montevideo
   - **Indica**: De qué caja sale el dinero

4. **Ingresá el "Monto UYU"**
   - Campo numérico
   - Placeholder: "0.00"
   - Monto en pesos uruguayos que retirás

5. **Ingresá el "Monto USD"**
   - Campo numérico
   - Placeholder: "0.00"
   - Monto en dólares que retirás
   - Podés poner UYU, USD o ambos

6. **Verificá el "Tipo de Cambio" (T.C.)**
   - Se carga automáticamente desde BCU
   - Se usa para calcular equivalencias

7. **Opcionalmente, escribí una "Descripción"**
   - Campo de texto
   - Placeholder: "Opcional"
   - Ejemplo: "Retiro mensual enero"

8. **Hacé clic en "Guardar"**
   - Mensaje: "✅ Retiro registrado correctamente"

---

## Campos del formulario

| Campo | Ubicación | Obligatorio | Tipo | Valor por defecto |
|-------|-----------|-------------|------|-------------------|
| Fecha | Fila 1, izquierda | ✅ | Calendario | Hoy |
| Localidad | Fila 1, derecha | ❌ | Desplegable | Montevideo |
| Monto UYU | Fila 2, izquierda | ❌* | Número | Vacío |
| Monto USD | Fila 2, centro | ❌* | Número | Vacío |
| T.C. | Fila 2, derecha | ✅ | Número | Auto BCU |
| Descripción | Fila 3 completa | ❌ | Texto | Vacío |

*Nota: Al menos uno de los montos (UYU o USD) debe tener valor.

---

## Ejemplos concretos

### Ejemplo 1: Retiro solo en pesos
**Situación**: Bruno retira $100.000 de la caja de Montevideo

**Datos a ingresar:**
- Fecha: (hoy)
- Localidad: Montevideo
- Monto UYU: 100000
- Monto USD: (vacío)
- T.C.: (automático)
- Descripción: Retiro mensual Bruno

**Resultado**: Se registra retiro de $100.000 UYU

### Ejemplo 2: Retiro solo en dólares
**Situación**: Agustina retira USD 500 de la caja de Mercedes

**Datos a ingresar:**
- Fecha: (hoy)
- Localidad: Mercedes
- Monto UYU: (vacío)
- Monto USD: 500
- T.C.: (automático, ej: 42.50)
- Descripción: Retiro Agustina

**Resultado**: Se registra retiro de USD 500 (equivalente ~$21.250 UYU)

### Ejemplo 3: Retiro mixto (pesos y dólares)
**Situación**: Gonzalo retira $50.000 en pesos y USD 200

**Datos a ingresar:**
- Fecha: (hoy)
- Localidad: Montevideo
- Monto UYU: 50000
- Monto USD: 200
- T.C.: (automático)
- Descripción: Retiro mixto Gonzalo

**Resultado**: Se registra retiro con ambos montos

---

## Explicación alternativa

Pensalo como ir a la caja del estudio y sacar dinero:

1. **¿Cuándo sacás?** → Fecha
2. **¿De qué caja?** → Localidad (MVD o Mercedes)
3. **¿Cuántos pesos?** → Monto UYU
4. **¿Cuántos dólares?** → Monto USD
5. **¿A qué cotización?** → Tipo de cambio
6. **¿Para qué?** → Descripción (opcional)

---

## Errores frecuentes y soluciones

### Error: "Solo socios pueden registrar retiros"
**Por qué aparece:** Intentaste registrar retiro pero tu cuenta es de colaborador
**Solución:** Solo los socios pueden hacer retiros. Contactá a un socio.

### Error: Ambos montos vacíos
**Por qué aparece:** No pusiste monto en UYU ni en USD
**Solución:** Completá al menos uno de los dos campos de monto

### Error: "No puedo ver el botón de Retiro"
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Los colaboradores no ven esta opción. Es normal.

---

## Preguntas frecuentes

### ¿Puedo hacer varios retiros en un mes?
Sí. No hay límite en la cantidad de retiros.

### ¿Cómo se ve después quién hizo el retiro?
El sistema registra qué usuario creó la operación. En descripción podés agregar el nombre.

### ¿Los retiros afectan las métricas?
Los retiros no son gastos ni ingresos. Afectan el flujo de caja pero no la rentabilidad operativa.

### ¿Puedo editar un retiro?
Sí. Desde el panel de Operaciones podés editar o eliminar retiros.

### ¿Cuál es la diferencia con distribución?
- **Retiro**: Un socio saca dinero
- **Distribución**: Se reparte entre los 5 socios formalmente

---

## Restricciones y limitaciones

- ❌ Solo socios pueden registrar retiros
- ❌ No puede ser fecha futura
- ❌ Debe tener al menos un monto (UYU o USD)

---

## Tips y recomendaciones

- 💡 Usá descripción para identificar de quién es el retiro
- 💡 Si retirás de la caja de Mercedes, seleccioná esa localidad
- 💡 Los retiros no tienen área asignada
- 💡 Consultá con el grupo antes de hacer retiros grandes
