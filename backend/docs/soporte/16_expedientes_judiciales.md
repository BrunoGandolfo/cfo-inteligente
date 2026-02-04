# Expedientes Judiciales

## Resumen rápido
El módulo de Expedientes Judiciales permite monitorear y gestionar expedientes del Poder Judicial de Uruguay directamente desde el sistema. Podés sincronizar expedientes, ver movimientos procesales, recibir notificaciones y generar resúmenes inteligentes con IA.

## ¿Qué es el módulo de Expedientes Judiciales?

Es una herramienta que se conecta directamente con el sistema web del Poder Judicial de Uruguay para obtener información actualizada de los expedientes que estás gestionando. El sistema sincroniza automáticamente los movimientos procesales y te notifica cuando hay novedades importantes.

## ¿Qué es un IUE?

El IUE (Identificador Único de Expediente) es el número que identifica cada expediente judicial en el sistema del Poder Judicial de Uruguay.

### Formato del IUE:
- Formato: Sede-Número/Año
- Ejemplo: 2-12345/2023
  - 2 = Sede (número del juzgado)
  - 12345 = Número del expediente
  - 2023 = Año

### ¿Dónde encontrarlo?
El IUE aparece en todos los documentos oficiales del expediente: escritos, decretos, resoluciones. También lo podés encontrar en el sistema web del Poder Judicial.

## Agregar un expediente nuevo

### Paso a paso:

1. **Hacé clic en "Agregar Expediente"**
   - Botón verde en la parte superior de la página
   - Se abre un modal (ventana emergente)

2. **Ingresá el IUE**
   - Formato: Sede-Número/Año (ej: 2-12345/2023)
   - El sistema valida el formato automáticamente

3. **Hacé clic en "Sincronizar"**
   - El sistema se conecta con el Poder Judicial
   - Busca el expediente y descarga toda la información disponible
   - Si el expediente existe, se agrega a tu lista
   - Si no existe o hay un error, te avisa

### ¿Qué pasa cuando se sincroniza?

Cuando sincronizás un expediente, el sistema:

- Se conecta con el servicio web del Poder Judicial de Uruguay
- Descarga la información básica del expediente:
  - Carátula (descripción del caso)
  - Origen (juzgado o sede)
  - Abogados (actor y demandado)
  - Estado actual
- Descarga todos los movimientos procesales:
  - Fechas de cada actuación
  - Tipo de movimiento (decreto, resolución, notificación, etc.)
  - Decretos y resoluciones
  - Fechas de vencimiento de plazos
  - Sede donde está el expediente
- Guarda todo en la base de datos del sistema
- Te muestra el expediente en la tabla principal

## Información que se obtiene

Cada expediente muestra:

- **IUE**: Identificador único
- **Carátula**: Descripción del caso
- **Origen**: Juzgado o sede de origen
- **Abogado Actor**: Abogado que inició el proceso
- **Abogado Demandado**: Abogado de la contraparte
- **Último Movimiento**: Fecha del último movimiento procesal
- **Cantidad de Movimientos**: Total de actuaciones registradas
- **Última Sincronización**: Cuándo se actualizó por última vez

## Sincronización automática

El sistema sincroniza automáticamente todos los expedientes activos:

- **Frecuencia**: Una vez al día
- **Hora**: 8:00 AM (hora de Montevideo, UTC-3)
- **Qué hace**: Consulta el Poder Judicial y descarga movimientos nuevos
- **Notificaciones**: Si hay movimientos nuevos, recibís una notificación por WhatsApp

No necesitás hacer nada, el sistema se encarga solo.

## Sincronización manual

Podés forzar una sincronización manual en cualquier momento:

### Para un expediente específico:

1. En la tabla de expedientes, encontrá el expediente que querés actualizar
2. Hacé clic en el botón "Re-sincronizar" en la fila correspondiente
3. El sistema consulta el Poder Judicial inmediatamente
4. Si hay movimientos nuevos, se actualizan automáticamente

### Para todos los expedientes:

1. Hacé clic en el botón "Sincronizar Todos" en la parte superior
2. El sistema sincroniza todos los expedientes activos uno por uno
3. Esto puede demorar varios minutos si tenés muchos expedientes
4. Se espera 1 segundo entre cada consulta para no sobrecargar el servicio

## Historia del expediente

La función "Ver Historia" genera un resumen inteligente usando inteligencia artificial que analiza todos los movimientos procesales.

### ¿Qué incluye el resumen?

- **Cronología**: Etapas principales del proceso en orden temporal
- **Estado Actual**: Dónde está el expediente ahora y qué implica
- **Hitos Importantes**: Decretos, resoluciones y actuaciones relevantes
- **Plazos**: Si hay plazos corriendo o vencidos
- **Próximos Pasos**: Sugerencias de qué actuaciones podrían corresponder

### Cómo usarlo:

1. En la tabla de expedientes, encontrá el expediente
2. Hacé clic en el botón "Ver Historia"
3. El sistema analiza todos los movimientos con IA
4. Se abre un modal con el resumen completo
5. Podés leer el análisis y cerrar cuando termines

## Notificaciones por WhatsApp

Cuando se detectan movimientos nuevos después de la sincronización automática, el sistema envía notificaciones automáticas por WhatsApp.

### ¿Qué incluyen las notificaciones?

- Resumen de los movimientos nuevos detectados
- Información del expediente (IUE y carátula)
- Fechas y tipos de movimientos
- Análisis inteligente generado por IA de los movimientos más relevantes

### Configuración:

Las notificaciones se configuran mediante variables de entorno en el servidor. Si necesitás agregar o modificar números de WhatsApp, contactá al administrador del sistema.

## Filtrado por responsable

Algunos usuarios ven solo los expedientes que tienen asignados como responsables. Esto significa que en la tabla solo aparecen los expedientes donde tu usuario está marcado como responsable.

Si necesitás ver un expediente que no aparece en tu lista, puede ser que:
- No esté asignado a vos como responsable
- Necesites que alguien con acceso completo lo asigne a tu nombre

## Asignar expediente a responsable, cliente y área

Podés asociar un expediente con:

- **Responsable**: Usuario del sistema que gestiona el expediente
- **Cliente**: Cliente del estudio relacionado con el caso
- **Área**: Área del estudio (Jurídica, Notarial, Contable, etc.)

### Cómo hacerlo:

1. Abrí el expediente desde la tabla
2. Usá las opciones de edición disponibles
3. Seleccioná el responsable, cliente y área correspondientes
4. Guardá los cambios

Esto ayuda a organizar mejor los expedientes y filtrarlos por responsable o área.

## Eliminar un expediente

Si necesitás eliminar un expediente:

1. En la tabla, encontrá el expediente que querés eliminar
2. Hacé clic en el botón "Eliminar"
3. Confirmá la acción
4. El expediente se marca como eliminado (soft delete)

**Importante**: Los movimientos procesales se mantienen en la base de datos, pero el expediente queda inactivo y no aparece en las listas.

## Cards de resumen

En la parte superior de la página hay tres cards que muestran estadísticas:

- **Total Activos**: Cantidad de expedientes activos en el sistema
- **Sincronizados Hoy**: Expedientes actualizados en las últimas 24 horas
- **Pendientes**: Expedientes con movimientos nuevos que requieren atención

## Información técnica

### Fuente de datos:
Los datos provienen directamente del sistema web del Poder Judicial de Uruguay mediante su servicio web oficial.

### Sincronización:
La sincronización automática se ejecuta diariamente a las 8:00 AM (hora de Montevideo, UTC-3) mediante un scheduler programado.

### Inteligencia Artificial:
El sistema utiliza Claude AI para analizar los movimientos procesales y generar resúmenes ejecutivos inteligentes que facilitan la comprensión del estado y evolución del expediente.

### Notificaciones:
Las notificaciones por WhatsApp se envían automáticamente cuando se detectan nuevos movimientos después de la sincronización diaria, utilizando la plataforma Twilio.

## Preguntas frecuentes

### ¿Cada cuánto se actualiza un expediente?
Los expedientes se actualizan automáticamente una vez al día a las 8:00 AM. También podés forzar una actualización manual en cualquier momento usando el botón de re-sincronización.

### ¿Qué pasa si el expediente tiene un error?
Si hay un error al sincronizar (por ejemplo, IUE inválido o problema de conexión), el sistema registrará el error en los logs. Podés intentar re-sincronizar manualmente. Si el problema persiste, verificá que el IUE sea correcto y que el expediente exista en el sistema del Poder Judicial.

### ¿Cómo interpretar los movimientos?
Cada movimiento representa una actuación procesal (decreto, resolución, notificación, etc.). Usá la función "Ver Historia" para obtener un análisis inteligente generado por IA que explica el contexto y significado de los movimientos en lenguaje claro.

### ¿Puedo agregar expedientes de cualquier sede?
Sí, podés agregar expedientes de cualquier sede del Poder Judicial de Uruguay. El sistema consulta automáticamente la información del expediente independientemente de su sede de origen.

### ¿Qué hago si no veo un expediente que debería estar?
Si un expediente no aparece en tu lista, puede ser que:
- No esté asignado a vos como responsable (si tu acceso está limitado)
- Esté eliminado o inactivo
- Haya un error en la sincronización

Contactá al administrador del sistema si necesitás ayuda.
