# Administrar Usuarios

## Resumen rápido
Permite ver la lista de usuarios del sistema y resetear contraseñas.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Sí |
| Colaborador | ❌ No |

## ¿Dónde está en la pantalla?

- **Ubicación**: Sidebar izquierdo → Parte inferior → "Administrar usuarios"
- **Ícono**: 👥 Usuarios (Users)
- **Color**: Púrpura
- **Acción**: Se abre un modal (ventana emergente)

---

## Cómo abrir la administración de usuarios

1. **En el sidebar izquierdo**, buscá abajo "Administrar usuarios"
2. **Hacé clic** en el botón
3. **Se abre un modal** con la lista de usuarios

---

## Elementos del modal

### Header:
- **Ícono**: 👥 Usuarios
- **Título**: "Administrar Usuarios"
- **Botón X**: Cierra el modal

### Tabla de usuarios:

| Columna | Contenido |
|---------|-----------|
| Usuario | Nombre del usuario |
| Email | Dirección de email |
| Rol | Badge "Socio" (púrpura) o "Colaborador" (gris) |
| Acciones | Botón "Resetear" |

### Footer:
- **Botón "Cerrar"**: Cierra el modal

---

## Ver lista de usuarios

Al abrir el modal, ves todos los usuarios activos del sistema:

| Nombre | Email | Rol |
|--------|-------|-----|
| Bruno Gandolfo | bgandolfo@cgmasociados.com | 🛡️ Socio |
| Agustina Borio | aborio@grupoconexion.uy | 🛡️ Socio |
| María García | mgarcia@grupoconexion.uy | Colaborador |
| ... | ... | ... |

---

## Resetear contraseña de un usuario

### ¿Cuándo usar?
- El usuario olvidó su contraseña
- El usuario no puede acceder

### Paso a paso:

1. **Abrí "Administrar usuarios"**
2. **Encontrá al usuario** en la tabla
3. **Hacé clic en "Resetear"** (botón naranja a la derecha)
4. **Confirmá**: "¿Resetear contraseña de [Nombre]?"
5. **Aceptá**
6. **Aparece la contraseña temporal** en un recuadro verde

### Contraseña temporal:
La nueva contraseña siempre es: **Temporal123**

### Después del reset:
1. **Comunicale** la contraseña temporal al usuario
2. **El usuario ingresa** con email + Temporal123
3. **El usuario debe cambiar** la contraseña inmediatamente

---

## Mensaje de contraseña reseteada

Cuando reseteas una contraseña, aparece:

```
┌─────────────────────────────────────────────────────────────┐
│ ✅ Contraseña reseteada para [Nombre]                       │
│                                                             │
│ Nueva contraseña temporal: Temporal123                      │
│                                                             │
│ El usuario deberá cambiarla en su próximo inicio de sesión. │
└─────────────────────────────────────────────────────────────┘
```

---

## Ejemplos concretos

### Ejemplo 1: Resetear contraseña de un colaborador
**Situación**: María olvidó su contraseña

1. Abrí "Administrar usuarios"
2. Buscá a María en la lista
3. Hacé clic en "Resetear"
4. Confirmá
5. Copiá "Temporal123"
6. Enviále el dato por otro medio (WhatsApp, llamada)
7. María entra con Temporal123 y la cambia

### Ejemplo 2: Verificar quién es socio
**Situación**: Querés ver qué usuarios son socios

1. Abrí "Administrar usuarios"
2. Mirá la columna "Rol"
3. Los socios tienen badge púrpura "🛡️ Socio"
4. Los colaboradores tienen badge gris "Colaborador"

---

## Restricciones

### No podés resetear tu propia contraseña
Si intentás resetear tu propia contraseña:

**Error**: "No puedes resetear tu propia contraseña. Usa 'Cambiar contraseña'"

**Solución**: Usá la opción "Cambiar contraseña" en el sidebar.

### No podés crear usuarios desde aquí
La creación de usuarios se hace desde la pantalla de registro pública.

### No podés eliminar usuarios
Actualmente no hay opción para desactivar usuarios desde esta pantalla.

---

## Errores frecuentes y soluciones

### Error: "Solo socios pueden ver la lista de usuarios"
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Solo socios tienen acceso a esta función

### Error: "No puedes resetear tu propia contraseña"
**Por qué aparece:** Intentaste resetearte a vos mismo
**Solución:** Usá "Cambiar contraseña" en el sidebar

### Error: "Usuario no encontrado"
**Por qué aparece:** El usuario fue desactivado
**Solución:** Contactá al administrador de la base de datos

### Error: "Error al cargar usuarios"
**Por qué aparece:** Problema de conexión con el servidor
**Solución:** Esperá unos segundos y recargá

---

## Preguntas frecuentes

### ¿Puedo cambiar el rol de un usuario (de colaborador a socio)?
No desde esta pantalla. Requiere modificación en la base de datos.

### ¿Puedo ver usuarios inactivos?
No. Solo se muestran usuarios activos.

### ¿La contraseña temporal expira?
No. El usuario puede usarla hasta que la cambie.

### ¿Es seguro usar siempre "Temporal123"?
Es una contraseña temporal que el usuario DEBE cambiar inmediatamente. Comunicala por un canal seguro.

### ¿Queda registro de quién reseteó una contraseña?
Actualmente no se registra explícitamente, pero queda en logs del servidor.

---

## Funciones que NO están disponibles

- ❌ Crear nuevos usuarios (se hace desde registro público)
- ❌ Cambiar rol de usuario
- ❌ Desactivar/eliminar usuarios
- ❌ Cambiar email de usuario
- ❌ Ver historial de accesos

---

## Tips y recomendaciones

- 💡 Antes de resetear, verificá que sea el usuario correcto
- 💡 Comunicá la contraseña temporal por un canal seguro (no email)
- 💡 Pedí al usuario que cambie la contraseña inmediatamente
- 💡 Si un usuario nuevo no puede entrar, verificá que se haya registrado
- 💡 Los socios autorizados se definen en la configuración del sistema
