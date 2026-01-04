# Panel de Operaciones

## Resumen rápido
El panel de Operaciones es donde podés ver, editar y eliminar todas las operaciones registradas en el sistema.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ❌ No |

## ¿Dónde está en la pantalla?

- **Ubicación**: Sidebar izquierdo → "Operaciones"
- **Ícono**: 📄 Documento (FileText)
- **Acción**: Se abre un panel lateral desde la derecha

---

## Cómo abrir el panel

1. **En el sidebar izquierdo**, buscá la opción "Operaciones"
2. **Hacé clic** en el botón
3. **Se abre un panel** que desliza desde la derecha
4. **El panel** muestra la lista de operaciones

---

## Elementos del panel

### Header del panel:
- **Ícono azul**: Documento
- **Título**: "Operaciones"
- **Subtítulo**: "Gestión de transacciones"
- **Botón X**: Cerrar panel (esquina superior derecha)

### Contenido:
- **Tabla de operaciones** con todas las transacciones
- **Filtrado** según los filtros del Dashboard (fecha, localidad)

---

## Tabla de operaciones

### Columnas:

| Columna | Contenido | Formato |
|---------|-----------|---------|
| Fecha | Fecha de la operación | DD/MM |
| Tipo | Badge con tipo | INGRESO / GASTO / RETIRO / DISTRIBUCIÓN |
| Cliente/Proveedor | Nombre | Texto |
| Monto | Valor en la moneda original | $ XX.XXX |
| Acciones | Botones | Editar / Eliminar |

### Badges por tipo:

| Tipo | Color |
|------|-------|
| INGRESO | Verde |
| GASTO | Rojo |
| RETIRO | Ámbar |
| DISTRIBUCIÓN | Azul |

---

## Ver detalles de una operación

### Paso a paso:
1. **En la tabla**, hacé clic en cualquier fila
2. **Se abre un modal** con los detalles completos
3. **Ves todos los campos** de la operación
4. **Cerrá** haciendo clic fuera o en el botón cerrar

### Información mostrada:
- Tipo de operación
- Fecha
- Montos (original, UYU, USD)
- Tipo de cambio
- Área
- Localidad
- Cliente o Proveedor
- Descripción

---

## Editar una operación

### Paso a paso:

1. **Encontrá la operación** en la tabla
2. **Hacé clic en "Editar"** (botón azul a la derecha)
3. **Se abre el modal** correspondiente (Ingreso, Gasto, Retiro o Distribución)
4. **El título cambia** a "Editar [Tipo]" en lugar de "Registrar [Tipo]"
5. **Los campos vienen precargados** con los valores actuales
6. **Modificá** los campos que necesites
7. **Hacé clic en "Actualizar"** (botón verde)
8. **Mensaje de éxito**: "✅ [Tipo] actualizado correctamente"

### Campos editables por tipo:

| Campo | Ingreso | Gasto | Retiro | Distribución |
|-------|---------|-------|--------|--------------|
| Fecha | ✅ | ✅ | ✅ | ✅ |
| Área | ✅ | ✅ | ❌ | ❌ |
| Localidad | ✅ | ✅ | ✅ | ✅ |
| Cliente | ✅ | ❌ | ❌ | ❌ |
| Proveedor | ❌ | ✅ | ❌ | ❌ |
| Monto | ✅ | ✅ | ✅ | ✅ |
| Moneda | ✅ | ✅ | ❌ | ❌ |
| Tipo cambio | ✅ | ✅ | ✅ | ✅ |
| Descripción | ✅ | ✅ | ✅ | ✅ |

---

## Eliminar una operación

### Paso a paso:

1. **Encontrá la operación** en la tabla
2. **Hacé clic en "Eliminar"** (botón rojo a la derecha)
3. **Aparece confirmación**: "¿Estás seguro de anular esta operación? Esta acción no se puede deshacer."
4. **Hacé clic en "Aceptar"** para confirmar
5. **La operación desaparece** de la lista
6. **Mensaje de éxito**: "Operación anulada correctamente"

### ¿Qué pasa realmente?

La operación NO se borra de la base de datos. Se marca como "anulada" (soft delete):
- Campo `deleted_at` recibe fecha/hora actual
- La operación deja de mostrarse en la lista
- No afecta las métricas
- Queda registro histórico en la base de datos

---

## Mensaje "No hay operaciones"

Si ves el mensaje "No hay operaciones en el período seleccionado":

### Posibles causas:
1. **No hay operaciones** registradas en ese rango de fechas
2. **Filtros muy restrictivos** - Verificá fecha desde/hasta
3. **Localidad filtrada** - Verificá que no esté filtrando solo una oficina

### Solución:
1. Ampliá el rango de fechas
2. Cambiá localidad a "Todas"
3. Registrá nuevas operaciones

---

## Ejemplos concretos

### Ejemplo 1: Corregir el monto de un ingreso
**Situación**: Cargaste $15.000 pero eran $16.000

1. Abrí el panel de Operaciones
2. Buscá el ingreso en la lista
3. Hacé clic en "Editar"
4. Cambiá el monto de 15000 a 16000
5. Hacé clic en "Actualizar"

### Ejemplo 2: Eliminar un gasto duplicado
**Situación**: Cargaste el mismo gasto dos veces

1. Abrí el panel de Operaciones
2. Identificá cuál es el duplicado
3. Hacé clic en "Eliminar"
4. Confirmá cuando pregunte

### Ejemplo 3: Cambiar el área de un ingreso
**Situación**: Pusiste "Jurídica" pero era "Contable"

1. Abrí el panel de Operaciones
2. Buscá el ingreso
3. Hacé clic en "Editar"
4. Cambiá el área de Jurídica a Contable
5. Hacé clic en "Actualizar"

---

## Errores frecuentes y soluciones

### Error: No veo el botón "Operaciones" en el sidebar
**Por qué aparece:** Sos colaborador, no socio
**Solución:** Solo socios ven el panel de Operaciones

### Error: No encuentro la operación que busco
**Por qué aparece:** Puede estar fuera del rango de fechas filtrado
**Solución:** Ampliá el rango de fechas en los filtros del Dashboard

### Error: "Operación no encontrada" al editar
**Por qué aparece:** La operación fue eliminada por otro usuario
**Solución:** Recargá la lista

---

## Preguntas frecuentes

### ¿Puedo ver operaciones eliminadas?
No. Las operaciones eliminadas (anuladas) no se muestran en la lista.

### ¿Puedo recuperar una operación eliminada?
No desde la interfaz. Un administrador de base de datos podría recuperarla.

### ¿Las ediciones quedan registradas?
Sí. Se actualiza el campo `updated_at` con la fecha de modificación.

### ¿Quién puede ver mis operaciones?
Todos los socios ven todas las operaciones del sistema.

### ¿Hay límite de operaciones mostradas?
Sí, se muestran hasta 50 operaciones. Las más recientes primero.

---

## Restricciones y limitaciones

- ❌ Solo socios pueden ver el panel de Operaciones
- ❌ Las operaciones eliminadas no se pueden recuperar desde la UI
- ❌ Límite de 50 operaciones en la lista

---

## Tips y recomendaciones

- 💡 Revisá las operaciones periódicamente para detectar errores
- 💡 Antes de eliminar, verificá que sea la operación correcta
- 💡 Usá los filtros del Dashboard para encontrar operaciones específicas
- 💡 Si no encontrás algo, ampliá el rango de fechas
- 💡 Las operaciones se ordenan por fecha (más recientes primero)
