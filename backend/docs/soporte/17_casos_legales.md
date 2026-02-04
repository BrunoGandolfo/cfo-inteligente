# Casos Legales

## Resumen rápido
El módulo de Casos Legales permite gestionar y hacer seguimiento de tareas legales, vencimientos y casos que necesitás monitorear. Podés crear casos, asignarles estados y prioridades, vincularlos con expedientes judiciales y hacer seguimiento de fechas de vencimiento.

## ¿Qué es el módulo de Casos Legales?

Es una herramienta para organizar y hacer seguimiento de casos legales, tareas y vencimientos importantes. Cada caso puede tener un estado, una prioridad, una fecha de vencimiento y estar vinculado con un expediente judicial del sistema.

## ¿Para qué sirve?

- Organizar casos y tareas legales en un solo lugar
- Hacer seguimiento de fechas de vencimiento importantes
- Priorizar casos según su urgencia
- Vincular casos con expedientes judiciales
- Mantener un registro del estado de cada caso
- Filtrar y buscar casos según diferentes criterios

## Crear un caso nuevo

### Paso a paso:

1. **Hacé clic en "Nuevo Caso"**
   - Botón azul en la parte superior de la página
   - Se abre un modal (ventana emergente) con el formulario

2. **Completá el título**
   - Campo obligatorio
   - Descripción breve del caso (ej: "Revisión contrato cliente ABC")
   - Máximo 300 caracteres

3. **Seleccioná el estado**
   - Opciones disponibles:
     - **Pendiente**: Caso creado pero aún no iniciado
     - **En Proceso**: Caso en desarrollo activo
     - **Requiere Acción**: Necesita atención urgente
     - **Cerrado**: Caso finalizado

4. **Seleccioná la prioridad**
   - Opciones disponibles:
     - **Crítica**: Máxima urgencia, requiere atención inmediata
     - **Alta**: Importante, atender pronto
     - **Media**: Prioridad normal
     - **Baja**: Puede esperar

5. **Opcional: Fecha de vencimiento**
   - Seleccioná una fecha del calendario
   - El sistema te avisará visualmente si está vencida
   - Útil para plazos procesales o fechas límite

6. **Opcional: IUE del Expediente**
   - Si el caso está relacionado con un expediente judicial
   - Ingresá el IUE en formato: Sede-Número/Año (ej: 2-12345/2023)
   - El sistema busca el expediente y lo vincula automáticamente
   - Si el expediente no existe, lo crea automáticamente

7. **Hacé clic en "Crear"**
   - El caso se guarda y aparece en la tabla
   - Se asigna automáticamente a vos como responsable

## Estados disponibles

Cada caso puede estar en uno de estos estados:

- **Pendiente**: El caso fue creado pero aún no se ha comenzado a trabajar en él. Es el estado inicial por defecto.

- **En Proceso**: El caso está siendo gestionado activamente. Hay trabajo en curso.

- **Requiere Acción**: El caso necesita atención urgente. Puede ser por un vencimiento próximo, una respuesta pendiente o alguna acción crítica.

- **Cerrado**: El caso está finalizado. Ya no requiere más trabajo.

Podés cambiar el estado en cualquier momento editando el caso.

## Prioridades

Las prioridades ayudan a organizar el trabajo según la urgencia:

- **Crítica**: Casos que requieren atención inmediata. Generalmente tienen vencimientos muy próximos o consecuencias graves si no se atienden.

- **Alta**: Casos importantes que deben atenderse pronto. Requieren seguimiento cercano.

- **Media**: Casos con prioridad normal. Se gestionan en el orden habitual de trabajo.

- **Baja**: Casos que pueden esperar. No tienen urgencia inmediata.

El sistema muestra las prioridades con colores diferentes para facilitar la identificación visual.

## Vincular un caso con un expediente

Si un caso está relacionado con un expediente judicial que ya existe en el sistema:

1. Al crear o editar el caso, ingresá el IUE del expediente
2. El sistema busca el expediente automáticamente
3. Si lo encuentra, lo vincula al caso
4. Si no existe, el sistema lo crea y sincroniza con el Poder Judicial

**Ventajas de vincular**:
- Podés ver información del expediente desde el caso
- El sistema mantiene la relación entre ambos
- Facilita el seguimiento integral del asunto legal

## Editar un caso

Para modificar un caso existente:

1. En la tabla de casos, encontrá el caso que querés editar
2. Hacé clic en el botón "Editar" (ícono de lápiz)
3. Se abre el mismo formulario con los datos actuales
4. Modificá los campos que necesites:
   - Título
   - Estado
   - Prioridad
   - Fecha de vencimiento
   - IUE del expediente
5. Hacé clic en "Actualizar"
6. Los cambios se guardan inmediatamente

**Nota**: El responsable del caso no se puede cambiar desde la edición. El caso siempre pertenece al usuario que lo creó.

## Eliminar un caso

Si necesitás eliminar un caso:

1. En la tabla, encontrá el caso que querés eliminar
2. Hacé clic en el botón "Eliminar" (ícono de papelera)
3. Confirmá la acción
4. El caso se marca como eliminado (soft delete)

**Importante**: El caso no se borra físicamente de la base de datos, solo se marca como eliminado y deja de aparecer en las listas. Esto permite mantener un historial.

## Filtrado por responsable

Algunos usuarios ven solo los casos que tienen asignados como responsables. Esto significa que en la tabla solo aparecen los casos donde tu usuario está marcado como responsable del caso.

Si creás un caso nuevo, automáticamente se asigna a vos como responsable. Solo podés ver y gestionar tus propios casos.

## Tabla de casos

La tabla muestra todos tus casos con esta información:

- **Título**: Nombre del caso
- **Estado**: Badge con el estado actual (Pendiente, En Proceso, etc.)
- **Prioridad**: Badge con la prioridad (Crítica, Alta, Media, Baja)
- **Fecha de Vencimiento**: Fecha límite del caso
  - Si está vencida, aparece en rojo con un ícono de alerta
  - Si está próxima a vencer, aparece destacada
- **Acciones**: Botones para editar o eliminar

Los casos se ordenan por fecha de creación (más recientes primero).

## Indicadores visuales

El sistema usa colores para facilitar la identificación:

- **Casos vencidos**: La fecha aparece en rojo con un ícono de alerta
- **Prioridad Crítica**: Badge rojo
- **Prioridad Alta**: Badge naranja
- **Prioridad Media**: Badge amarillo
- **Prioridad Baja**: Badge verde
- **Estado Cerrado**: Badge verde
- **Estado Requiere Acción**: Badge naranja

## Filtros disponibles

Podés filtrar los casos por:

- **Estado**: Ver solo casos en un estado específico (Pendiente, En Proceso, etc.)
- **Prioridad**: Ver solo casos de una prioridad determinada (Crítica, Alta, etc.)

Los filtros se aplican combinados: podés ver, por ejemplo, solo los casos "En Proceso" con prioridad "Alta".

## Preguntas frecuentes

### ¿Puedo cambiar el responsable de un caso?
No, el responsable siempre es el usuario que creó el caso. Si necesitás transferir un caso a otro usuario, contactá al administrador del sistema.

### ¿Qué pasa si elimino un caso por error?
Los casos eliminados se marcan como eliminados pero no se borran físicamente. Contactá al administrador si necesitás recuperar un caso eliminado por error.

### ¿Puedo crear casos sin vincularlos a un expediente?
Sí, el IUE del expediente es opcional. Podés crear casos para cualquier tarea legal, incluso si no está relacionada con un expediente judicial.

### ¿Cómo sé si un caso está vencido?
El sistema muestra la fecha de vencimiento en rojo con un ícono de alerta si la fecha ya pasó. También podés ordenar los casos por fecha de vencimiento para ver cuáles están próximos a vencer.

### ¿Puedo tener varios casos vinculados al mismo expediente?
Sí, un expediente puede tener múltiples casos asociados. Esto es útil cuando un expediente tiene varias tareas o aspectos diferentes que necesitás gestionar por separado.
