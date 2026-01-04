# Errores Comunes y Soluciones

## Resumen rápido
Esta guía lista todos los errores que pueden aparecer en el sistema y cómo resolverlos.

---

## Errores de Autenticación

### "Credenciales incorrectas" / "Email o contraseña incorrectos"
**Dónde aparece:** Login
**Por qué aparece:** El email o la contraseña están mal escritos
**Solución:**
1. Verificá que el email esté bien escrito
2. Verificá mayúsculas/minúsculas en la contraseña
3. Si olvidaste la contraseña, pedí reset a un socio

### "Usuario desactivado"
**Dónde aparece:** Login
**Por qué aparece:** Tu cuenta fue desactivada
**Solución:** Contactá a bgandolfo@cgmasociados.com

### "Token inválido o expirado"
**Dónde aparece:** Cualquier pantalla
**Por qué aparece:** Tu sesión expiró
**Solución:** El sistema te redirige a login. Volvé a ingresar.

---

## Errores de Registro

### "Las contraseñas no coinciden"
**Dónde aparece:** Registro
**Por qué aparece:** Los campos Contraseña y Confirmar son diferentes
**Solución:** Escribí exactamente la misma contraseña en ambos campos

### "Este usuario ya está registrado"
**Dónde aparece:** Registro
**Por qué aparece:** Ya existe una cuenta con ese email
**Solución:** Usá "Iniciar Sesión" en lugar de "Registrarse"

### "El usuario de email es requerido"
**Dónde aparece:** Registro
**Por qué aparece:** El campo usuario está vacío
**Solución:** Escribí tu usuario (sin @)

### "Solo ingresa tu usuario, sin @"
**Dónde aparece:** Registro
**Por qué aparece:** Escribiste @ en el campo usuario
**Solución:** Solo escribí el prefijo, sin @. Ejemplo: "jperez" no "jperez@"

### "La contraseña debe tener al menos 6 caracteres"
**Dónde aparece:** Registro o Cambiar contraseña
**Por qué aparece:** La contraseña es muy corta
**Solución:** Usá una contraseña de 6 o más caracteres

---

## Errores de Operaciones

### "Campo obligatorio" en Área
**Dónde aparece:** Modal de Ingreso/Gasto
**Por qué aparece:** No seleccionaste un área
**Solución:** Hacé clic en el desplegable de Área y elegí una opción

### "Campo obligatorio" en Cliente/Proveedor
**Dónde aparece:** Modal de Ingreso/Gasto
**Por qué aparece:** El campo está vacío
**Solución:** Escribí el nombre del cliente o proveedor

### "Campo obligatorio" en Monto
**Dónde aparece:** Modal de Ingreso/Gasto/Retiro
**Por qué aparece:** No ingresaste el monto
**Solución:** Escribí el valor numérico

### "Solo socios pueden registrar retiros"
**Dónde aparece:** Al intentar crear retiro
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Solo los socios pueden registrar retiros

### "Solo socios pueden registrar distribuciones"
**Dónde aparece:** Al intentar crear distribución
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Solo los socios pueden registrar distribuciones

### "ID inválido"
**Dónde aparece:** Al editar/eliminar operación
**Por qué aparece:** Error interno del sistema
**Solución:** Recargá la página e intentá de nuevo

### "Operación no encontrada"
**Dónde aparece:** Al editar/eliminar operación
**Por qué aparece:** La operación fue eliminada por otro usuario
**Solución:** Recargá la lista de operaciones

---

## Errores de Permisos

### "Solo socios pueden ver la lista de usuarios"
**Dónde aparece:** Administrar usuarios
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Solo socios tienen acceso a esta función

### "Solo socios pueden resetear contraseñas"
**Dónde aparece:** Administrar usuarios
**Por qué aparece:** Tu cuenta es de colaborador
**Solución:** Solo socios pueden resetear contraseñas

### "No puedes resetear tu propia contraseña"
**Dónde aparece:** Administrar usuarios
**Por qué aparece:** Intentaste resetearte a vos mismo
**Solución:** Usá "Cambiar contraseña" en el sidebar

---

## Errores de Contraseña

### "La contraseña actual es requerida"
**Dónde aparece:** Cambiar contraseña
**Por qué aparece:** El campo está vacío
**Solución:** Completá tu contraseña actual

### "La nueva contraseña es requerida"
**Dónde aparece:** Cambiar contraseña
**Por qué aparece:** El campo está vacío
**Solución:** Escribí una nueva contraseña

### "La nueva contraseña debe ser diferente a la actual"
**Dónde aparece:** Cambiar contraseña
**Por qué aparece:** Pusiste la misma contraseña
**Solución:** Elegí una contraseña distinta

### "Contraseña actual incorrecta"
**Dónde aparece:** Cambiar contraseña
**Por qué aparece:** La contraseña actual está mal
**Solución:** Verificá que estés escribiendo bien tu contraseña actual

---

## Errores de Conexión

### "Error al cargar operaciones"
**Dónde aparece:** Panel de Operaciones
**Por qué aparece:** Problema de conexión con el servidor
**Solución:** Verificá tu conexión a internet y recargá la página

### "Error al cargar usuarios"
**Dónde aparece:** Administrar usuarios
**Por qué aparece:** Problema de conexión con el servidor
**Solución:** Esperá unos segundos y recargá

### "Error de conexión"
**Dónde aparece:** Cualquier acción
**Por qué aparece:** No hay conexión con el servidor
**Solución:**
1. Verificá tu conexión a internet
2. Esperá unos segundos
3. Recargá la página
4. Si persiste, contactá soporte

### Pantalla de "Cargando..." permanente
**Dónde aparece:** Dashboard u otras pantallas
**Por qué aparece:** Problema de conexión o error del servidor
**Solución:** Recargá la página (F5 o Ctrl+R)

---

## Errores del CFO AI

### El chat no responde
**Por qué aparece:** Problema de conexión o el servicio está ocupado
**Solución:** Esperá unos segundos y reintentá

### La respuesta está incompleta
**Por qué aparece:** Límite de respuesta del asistente
**Solución:** Hacé una pregunta más específica

### "Límite de conversación alcanzado"
**Por qué aparece:** Llegaste a 27+ mensajes
**Solución:** Hacé clic en "🔄 Nueva conversación"

---

## Errores de Exportación PDF

### Error al exportar PDF
**Dónde aparece:** CFO AI, botón exportar
**Por qué aparece:** Problema al generar el archivo
**Solución:** Intentá de nuevo. Si persiste, copiá el texto manualmente.

---

## Errores de Filtros

### Métricas muestran $0
**Por qué aparece:** No hay operaciones en el período filtrado
**Solución:** Ampliá el rango de fechas o verificá los filtros

### "No hay operaciones en el período seleccionado"
**Por qué aparece:** Los filtros excluyen todas las operaciones
**Solución:**
1. Ampliá el rango de fechas
2. Cambiá localidad a "Todas"
3. Verificá que haya operaciones cargadas

---

## Si el error persiste

### Pasos generales de solución:
1. **Recargá la página** (F5 o Ctrl+R)
2. **Cerrá y volvé a abrir el navegador**
3. **Cerrá sesión y volvé a entrar**
4. **Probá desde otro navegador**
5. **Contactá a soporte**: bgandolfo@cgmasociados.com

### Información para reportar un error:
- ¿Qué estabas haciendo?
- ¿Qué mensaje de error apareció?
- ¿En qué pantalla estabas?
- ¿Qué navegador usás?
- ¿Es la primera vez que pasa?
