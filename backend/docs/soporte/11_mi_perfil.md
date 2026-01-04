# Mi Perfil - Cambiar Contraseña

## Resumen rápido
Desde tu perfil podés cambiar tu contraseña de acceso al sistema.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ✅ Sí |

## ¿Dónde está en la pantalla?

- **Ubicación**: Sidebar izquierdo → Parte inferior → "Cambiar contraseña"
- **Ícono**: 🔒 Candado (Lock)
- **Color**: Gris
- **Acción**: Se abre un modal (ventana emergente)

---

## Cambiar contraseña

### Cuándo cambiar tu contraseña:
- Después de un reset (contraseña temporal)
- Periódicamente por seguridad
- Si sospechás que alguien conoce tu contraseña

### Paso a paso:

1. **En el sidebar izquierdo**, buscá "Cambiar contraseña"
2. **Hacé clic** en el botón
3. **Se abre un modal** con el formulario
4. **Completá los campos**:
   - Contraseña actual
   - Nueva contraseña
   - Confirmar nueva contraseña
5. **Hacé clic en "Guardar"**

---

## Campos del formulario

| Campo | Ícono | Obligatorio | Placeholder | Validaciones |
|-------|-------|-------------|-------------|--------------|
| Contraseña actual | 🔒 | ✅ | "Tu contraseña actual" | Debe ser correcta |
| Nueva contraseña | 🔒 | ✅ | "Mínimo 6 caracteres" | Mínimo 6 caracteres, diferente a la actual |
| Confirmar nueva | 🔒 | ✅ | "Repetir nueva contraseña" | Debe coincidir |

---

## Validaciones

El sistema valida:

| Validación | Mensaje de error |
|------------|------------------|
| Contraseña actual vacía | "La contraseña actual es requerida" |
| Nueva contraseña vacía | "La nueva contraseña es requerida" |
| Nueva contraseña muy corta | "La nueva contraseña debe tener al menos 6 caracteres" |
| Nueva igual a actual | "La nueva contraseña debe ser diferente a la actual" |
| Confirmación no coincide | "Las contraseñas no coinciden" |
| Contraseña actual incorrecta | "Contraseña actual incorrecta" |

---

## Ejemplo: Cambiar contraseña después de reset

**Situación**: Un socio te reseteó la contraseña a "Temporal123"

**Datos a ingresar:**
- Contraseña actual: Temporal123
- Nueva contraseña: MiNuevaContraseña2026
- Confirmar nueva: MiNuevaContraseña2026

**Resultado**: "Contraseña actualizada correctamente"

---

## Botones del formulario

| Botón | Color | Ubicación | Acción |
|-------|-------|-----------|--------|
| Cancelar | Gris/borde | Izquierda | Cierra sin guardar |
| Guardar | Índigo | Derecha | Guarda la nueva contraseña |

---

## Errores frecuentes y soluciones

### Error: "La contraseña actual es requerida"
**Solución:** Completá el campo de contraseña actual

### Error: "La nueva contraseña debe tener al menos 6 caracteres"
**Solución:** Usá una contraseña más larga (mínimo 6 caracteres)

### Error: "La nueva contraseña debe ser diferente a la actual"
**Solución:** Elegí una contraseña distinta a la que tenés

### Error: "Las contraseñas no coinciden"
**Solución:** Verificá que "Nueva contraseña" y "Confirmar" sean idénticas

### Error: "Contraseña actual incorrecta"
**Solución:** Verificá que estés escribiendo bien tu contraseña actual

---

## Preguntas frecuentes

### ¿Qué pasa si olvido mi contraseña?
Pedí a un socio que te la resetee desde "Administrar usuarios".

### ¿Hay requisitos especiales para la contraseña?
Solo debe tener mínimo 6 caracteres. No hay requisitos de mayúsculas, números o símbolos.

### ¿Cada cuánto debo cambiar mi contraseña?
No hay requisito obligatorio, pero se recomienda cada 3-6 meses.

### ¿Puedo usar la misma contraseña que antes?
No. La nueva contraseña debe ser diferente a la actual.

---

## Tips y recomendaciones

- 💡 Usá una contraseña que puedas recordar
- 💡 No uses datos personales obvios (cumpleaños, nombres)
- 💡 No compartas tu contraseña con nadie
- 💡 Cambiá la contraseña si sospechás que alguien la conoce
- 💡 Después de un reset, cambiá "Temporal123" inmediatamente
