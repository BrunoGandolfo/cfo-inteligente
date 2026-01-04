# Dashboard Principal

## Resumen rápido
El Dashboard es la pantalla principal del sistema donde ves las métricas financieras, gráficos y accesos rápidos para registrar operaciones.

## ¿Quién puede usarlo?
| Rol | Acceso |
|-----|--------|
| Socio | ✅ Dashboard completo con métricas |
| Colaborador | ✅ Vista simplificada (ver sección Colaboradores) |

## ¿Dónde está en la pantalla?

Es la primera pantalla que ves después de loguearte. URL: `/dashboard`

---

## Layout general (para socios)

### Estructura de la pantalla:

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER (fijo arriba)                                            │
│ Logo | Fecha/Hora | Filtros | Usuario | Cerrar sesión           │
├───────────┬─────────────────────────────────────────────────────┤
│           │                                                     │
│  SIDEBAR  │  CONTENIDO PRINCIPAL                               │
│  (menú    │                                                     │
│   lateral)│  ┌─────────────────────────────────────────────┐  │
│           │  │  MÉTRICAS (4 cards)                          │  │
│           │  │  Ingresos | Gastos | Rentabilidad | Área    │  │
│           │  └─────────────────────────────────────────────┘  │
│           │                                                     │
│           │  ┌─────────────────────────────────────────────┐  │
│           │  │  FILTROS ACTIVOS                            │  │
│           │  └─────────────────────────────────────────────┘  │
│           │                                                     │
│           │  ┌─────────────────────────────────────────────┐  │
│           │  │  GRÁFICOS                                   │  │
│           │  └─────────────────────────────────────────────┘  │
│           │                                                     │
│           │  ┌─────────────────────────────────────────────┐  │
│           │  │  REGISTRAR OPERACIÓN (4 botones)           │  │
│           │  │  Ingreso | Gasto | Retiro | Distribución   │  │
│           │  └─────────────────────────────────────────────┘  │
│           │                                                     │
└───────────┴─────────────────────────────────────────────────────┘
```

---

## Header (barra superior)

### Elementos del Header:

| Elemento | Ubicación | Descripción |
|----------|-----------|-------------|
| Logo Conexión | Izquierda | Logo de la empresa |
| Fecha y hora | Centro | Muestra fecha actual y hora (actualización cada minuto) |
| Botón Filtros | Centro | Abre drawer con filtros (pantallas pequeñas) |
| Filtros inline | Centro | Fecha, localidad, moneda (pantallas grandes) |
| Campana | Derecha | Notificaciones (próximamente) |
| Tema | Derecha | Cambiar entre modo claro/oscuro |
| Avatar | Derecha | Inicial del nombre del usuario |
| "Hola, [nombre]" | Derecha | Saludo personalizado |
| Cerrar sesión | Derecha | Botón rojo para salir |

### Filtros disponibles:

| Filtro | Opciones | Valor por defecto |
|--------|----------|-------------------|
| Moneda | UYU / USD | UYU |
| Fecha desde | Calendario | Primer día del mes |
| Fecha hasta | Calendario | Hoy |
| Localidad | Todas / Montevideo / Mercedes | Todas |

---

## Sidebar (menú lateral izquierdo)

### Opciones del menú:

| Opción | Ícono | Descripción | Acción |
|--------|-------|-------------|--------|
| Dashboard | 🏠 Casa | Pantalla principal | Ya estás aquí |
| Operaciones | 📄 Documento | Panel de operaciones | Abre panel derecho |
| CFO AI | ✨ Estrella | Chat con asistente AI | Abre panel derecho |
| Configuración | ⚙️ Engranaje | Opciones (próximamente) | - |

### Opciones adicionales (parte inferior):

| Opción | Ícono | Descripción | Quién ve |
|--------|-------|-------------|----------|
| Administrar usuarios | 👥 Usuarios | Gestión de usuarios | Solo socios |
| Cambiar contraseña | 🔒 Candado | Cambiar tu contraseña | Todos |

---

## Métricas (4 cards superiores)

### Card 1: Ingresos del mes
- **Color borde**: Verde (border-green-500)
- **Ícono**: Flecha hacia arriba (TrendingUp)
- **Valor**: Monto total de ingresos del período filtrado
- **Formato**: $ XX.XXX,XX (según moneda seleccionada)

### Card 2: Gastos del mes
- **Color borde**: Rojo (border-red-500)
- **Ícono**: Flecha hacia abajo (TrendingDown)
- **Valor**: Monto total de gastos del período filtrado
- **Formato**: $ XX.XXX,XX (según moneda seleccionada)

### Card 3: Rentabilidad
- **Color borde**: Azul (border-blue-500)
- **Ícono**: Gráfico de líneas (LineChart)
- **Valor**: Porcentaje de margen operativo
- **Formato**: XX.XX%
- **Cálculo**: ((Ingresos - Gastos) / Ingresos) × 100

### Card 4: Área líder
- **Color borde**: Púrpura (border-purple-500)
- **Ícono**: Trofeo (Trophy)
- **Valor**: Nombre del área con mayor facturación
- **Ejemplo**: "Jurídica" o "Contable"

---

## Filtros activos

Cuando tenés filtros aplicados distintos a los por defecto, aparece una barra debajo de las métricas:

```
Filtros activos: [01/12 - 31/12 ×] [Montevideo ×] [UYU]
```

- **Badge azul**: Rango de fechas (click en × para resetear)
- **Badge púrpura**: Localidad (click en × para resetear)
- **Badge verde**: Moneda seleccionada

---

## Gráficos

El sistema muestra gráficos interactivos con los datos del período seleccionado:

1. **Gráfico de barras**: Comparación de ingresos vs gastos
2. **Gráfico de líneas**: Evolución temporal
3. **Gráfico de torta**: Distribución por áreas

---

## Sección "Registrar Operación"

### 4 botones de acción:

| Botón | Color | Ícono | Descripción | Atajo |
|-------|-------|-------|-------------|-------|
| Registrar Ingreso | Verde | ↗️ TrendingUp | Cobros y ventas | ⌘ + 1 |
| Registrar Gasto | Rojo | ↘️ TrendingDown | Gastos operativos | ⌘ + 2 |
| Retiro de Empresa | Ámbar | 💰 Wallet | Retiros de socios | ⌘ + 3 |
| Distribución de Utilidades | Azul | 👥 Users | Reparto entre socios | ⌘ + 4 |

### Información en cada botón:

- **Título**: Nombre de la operación
- **Descripción**: Explicación breve
- **Última actividad**: Monto acumulado del mes o mensaje informativo
- **Atajo de teclado**: Combinación para acceso rápido

---

## Vista de Colaborador

Los colaboradores ven una pantalla simplificada:

### Diferencias con la vista de socio:

| Elemento | Socio | Colaborador |
|----------|-------|-------------|
| Métricas financieras | ✅ Sí | ❌ No |
| Gráficos | ✅ Sí | ❌ No |
| Botón Retiro | ✅ Sí | ❌ No |
| Botón Distribución | ✅ Sí | ❌ No |
| Sidebar completo | ✅ Sí | ❌ No |
| Filtros | ✅ Sí | ❌ No |

### Pantalla del colaborador:

```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER: Bienvenido, [Nombre] | Fecha | Tema | Cerrar sesión     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│           ┌──────────────┐    ┌──────────────┐                  │
│           │  REGISTRAR   │    │  REGISTRAR   │                  │
│           │   INGRESO    │    │    GASTO     │                  │
│           │      ↗️       │    │      ↘️       │                  │
│           └──────────────┘    └──────────────┘                  │
│                                                                  │
│           ┌───────────────────────────────────┐                  │
│           │  📅 Operaciones este mes: 25      │                  │
│           │  "¡A seguir registrando!"         │                  │
│           └───────────────────────────────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Ejemplos concretos

### Ejemplo 1: Ver cuánto se facturó en enero
1. Abrí los filtros
2. Poné fecha desde: 01/01/2026
3. Poné fecha hasta: 31/01/2026
4. Mirá la card "Ingresos del mes"

### Ejemplo 2: Ver solo operaciones de Mercedes
1. En el filtro de Localidad, seleccioná "Mercedes"
2. Todas las métricas y gráficos se actualizan
3. Aparece badge púrpura "Mercedes" en filtros activos

### Ejemplo 3: Ver valores en dólares
1. Hacé clic en el toggle de moneda
2. Cambiá de "UYU" a "USD"
3. Todos los montos se muestran convertidos a dólares

---

## Errores frecuentes y soluciones

### Error: "Cargando..." permanente
**Por qué aparece:** Problema de conexión con el servidor
**Solución:** Recargá la página (F5 o Ctrl+R)

### Error: Métricas muestran $0
**Por qué aparece:** No hay operaciones en el período seleccionado
**Solución:** Verificá los filtros de fecha, podés estar viendo un mes sin actividad

### Error: Gráficos no cargan
**Por qué aparece:** No hay datos suficientes
**Solución:** Ampliá el rango de fechas o verificá que haya operaciones cargadas

---

## Preguntas frecuentes

### ¿Cada cuánto se actualizan las métricas?
Las métricas se actualizan cada vez que:
- Cargás la página
- Registrás una operación
- Cambiás los filtros

### ¿Puedo exportar los datos del Dashboard?
Actualmente no hay opción de exportar. Podés pedir reportes al CFO AI.

### ¿Por qué veo valores diferentes que otro socio?
Verificá que ambos tengan los mismos filtros (fecha, localidad, moneda).

---

## Tips y recomendaciones

- 💡 Revisá el Dashboard al inicio del día para ver el estado financiero
- 💡 Usá los filtros para comparar períodos (este mes vs mes anterior)
- 💡 El área líder te indica dónde está el mejor desempeño
- 💡 Si la rentabilidad es negativa, los gastos superan a los ingresos
