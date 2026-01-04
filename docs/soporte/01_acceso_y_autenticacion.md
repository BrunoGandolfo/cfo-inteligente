# Acceso y Autenticación

## Resumen rápido
Esta sección explica cómo ingresar al sistema, crear una cuenta nueva y gestionar tu contraseña.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Puede registrarse y loguearse |
| Colaborador | ✅ Puede registrarse y loguearse |

## ¿Dónde está en la pantalla?

La pantalla de acceso es la primera que ves al entrar a **www.cfointeligente.com**

### Elementos de la pantalla de inicio:

- **Izquierda**: Hero con título "CFO Inteligente" y descripción del sistema
- **Derecha**: Card con formularios de Login y Registro
- **Arriba derecha**: Indicador "Sistema Online" con punto verde
- **Abajo**: Capacidades del sistema y footer

---

## Iniciar Sesión (Login)

### Paso a paso detallado

1. **Abrí el navegador** y andá a www.cfointeligente.com
2. **Verificá que la pestaña "Iniciar Sesión" esté activa** - Tiene una línea azul debajo
3. **Ingresá tu email** en el campo "Email"
   - Placeholder: "tu@conexionconsultora.uy"
   - Formato: usuario@dominio.com
4. **Ingresá tu contraseña** en el campo "Contraseña"
   - Placeholder: "••••••••"
   - Los caracteres se ocultan por seguridad
5. **Opcionalmente, marcá "Recordarme"** - Checkbox a la izquierda
6. **Hacé clic en "Ingresar al Sistema"** - Botón azul grande

### Campos del formulario de Login

| Campo | Ubicación | Obligatorio | Tipo | Ejemplo |
|-------|-----------|-------------|------|---------|
| Email | Arriba | ✅ Sí | Email | bgandolfo@cgmasociados.com |
| Contraseña | Abajo | ✅ Sí | Password | ••••••••• |
| Recordarme | Debajo de contraseña | ❌ No | Checkbox | - |

### ¿Qué pasa después de loguearte?

- **Si las credenciales son correctas**: 
  - Aparece mensaje verde "Bienvenido al sistema"
  - Redirige automáticamente al Dashboard
- **Si las credenciales son incorrectas**:
  - Aparece mensaje rojo "Credenciales incorrectas"
  - Permanecés en la pantalla de login

---

## Registrarse (Crear cuenta nueva)

### Paso a paso detallado

1. **En la pantalla de inicio**, hacé clic en el botón "Registrarse" (arriba a la derecha del card)
2. **Completá el campo "Nombre completo"**
   - Placeholder: "Juan Pérez"
   - Tu nombre real como aparecerá en el sistema
3. **Completá el campo "Usuario"**
   - Escribí solo tu usuario (sin @)
   - El dominio @grupoconexion.uy se agrega automáticamente
   - Si sos bgandolfo, el dominio será @cgmasociados.com
4. **Ingresá una contraseña** en "Contraseña"
   - Mínimo 6 caracteres
5. **Confirmá la contraseña** en "Confirmar Contraseña"
   - Debe ser idéntica a la anterior
6. **Hacé clic en "Crear Cuenta"** - Botón verde

### Campos del formulario de Registro

| Campo | Ubicación | Obligatorio | Tipo | Reglas | Ejemplo |
|-------|-----------|-------------|------|--------|---------|
| Nombre completo | 1ro | ✅ Sí | Texto | - | Bruno Gandolfo |
| Usuario | 2do | ✅ Sí | Texto con dominio | Sin @, sin espacios | bgandolfo |
| Contraseña | 3ro | ✅ Sí | Password | Mínimo 6 caracteres | ••••••• |
| Confirmar Contraseña | 4to | ✅ Sí | Password | Debe coincidir | ••••••• |

### Sistema de dominios

| Si tu usuario es... | Tu email será... | Rol asignado |
|---------------------|------------------|--------------|
| aborio | aborio@grupoconexion.uy | Socio |
| falgorta | falgorta@grupoconexion.uy | Socio |
| vcaresani | vcaresani@grupoconexion.uy | Socio |
| gtaborda | gtaborda@grupoconexion.uy | Socio |
| bgandolfo | bgandolfo@cgmasociados.com | Socio |
| cualquier otro | usuario@grupoconexion.uy | Colaborador |

### ¿Qué pasa después de registrarte?

- **Si todo está correcto**:
  - Aparece mensaje verde "Cuenta creada exitosamente. Ya puedes iniciar sesión."
  - Te lleva automáticamente a la pestaña de Login
  - Ahora podés ingresar con tu email y contraseña
- **Si hay errores**:
  - "Las contraseñas no coinciden" - Revisá que ambas contraseñas sean iguales
  - "Este usuario ya está registrado" - Ya existe una cuenta con ese email
  - "El usuario de email es requerido" - Completá el campo Usuario
  - "La contraseña debe tener al menos 6 caracteres" - Usá una contraseña más larga

---

## Olvidé mi contraseña

### ¿Dónde está?
En la pantalla de Login, debajo del campo contraseña, hay un link "¿Olvidaste tu contraseña?"

### ¿Qué hace?
Muestra un mensaje: "Contacta al administrador del sistema para restablecer tu contraseña."

### ¿Cómo recuperar la contraseña?
1. Contactá a un socio del sistema
2. El socio puede resetear tu contraseña desde "Administrar usuarios"
3. Te darán una contraseña temporal: **Temporal123**
4. Ingresá con esa contraseña y cambiála inmediatamente

---

## Cerrar Sesión

### ¿Dónde está el botón?
- **Para socios**: Arriba a la derecha, botón rojo "Cerrar sesión"
- **Para colaboradores**: Arriba a la derecha, botón rojo "Cerrar sesión"

### Paso a paso
1. **Hacé clic en "Cerrar sesión"** (botón rojo con borde)
2. **Aparece mensaje verde** "Sesión cerrada correctamente"
3. **Redirige a la pantalla de login** automáticamente

---

## Errores frecuentes y soluciones

### Error: "Credenciales incorrectas"
**Por qué aparece:** El email o la contraseña están mal
**Solución:** 
- Verificá que el email esté bien escrito
- Verificá mayúsculas/minúsculas en la contraseña
- Si olvidaste la contraseña, pedí reset a un socio

### Error: "Usuario desactivado"
**Por qué aparece:** Tu cuenta fue desactivada por un administrador
**Solución:** Contactá a bgandolfo@cgmasociados.com

### Error: "Las contraseñas no coinciden"
**Por qué aparece:** Al registrarte, los campos Contraseña y Confirmar Contraseña son diferentes
**Solución:** Escribí la misma contraseña en ambos campos

### Error: "Este usuario ya está registrado"
**Por qué aparece:** Ya existe una cuenta con ese email
**Solución:** Usá la opción "Iniciar Sesión" en lugar de "Registrarse"

### Error: "La contraseña debe tener al menos 6 caracteres"
**Por qué aparece:** La contraseña es muy corta
**Solución:** Usá una contraseña de 6 o más caracteres

---

## Preguntas frecuentes

### ¿Puedo cambiar mi email?
No. El email se asigna según tu usuario y no se puede modificar después de registrarte.

### ¿Cómo sé si soy socio o colaborador?
- Al registrarte, aparece un mensaje indicando tu rol
- Los socios ven el Dashboard completo con métricas
- Los colaboradores ven una pantalla simplificada

### ¿Mi sesión expira?
Sí. Si no usás el sistema por un tiempo prolongado, tendrás que volver a loguearte.

### ¿Puedo tener varias sesiones abiertas?
Sí, podés usar el sistema desde varios dispositivos al mismo tiempo.

---

## Tips y recomendaciones

- 💡 Usá una contraseña segura que puedas recordar
- 💡 Marcá "Recordarme" si usás tu computadora personal
- 💡 No compartas tu contraseña con nadie
- 💡 Si compartís computadora, cerrá sesión al terminar
