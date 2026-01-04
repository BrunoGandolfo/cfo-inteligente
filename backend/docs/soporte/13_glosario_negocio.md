# Glosario de Términos

## Resumen rápido
Definiciones de todos los términos usados en el sistema CFO Inteligente.

---

## Términos Financieros

### Ingreso
**Definición:** Dinero que entra al estudio por servicios prestados.
**Ejemplos:** Cobro de honorarios, pago de un cliente, facturación.
**En el sistema:** Se registra con fecha, cliente, área, monto y descripción.

### Gasto
**Definición:** Dinero que sale del estudio para pagar servicios u obligaciones.
**Ejemplos:** Pago de alquiler, luz, agua, honorarios a terceros.
**En el sistema:** Se registra con fecha, proveedor, área, monto y descripción.

### Retiro
**Definición:** Dinero que un socio extrae del estudio para uso personal.
**Diferencia con gasto:** El gasto es para la operación; el retiro es para el socio.
**En el sistema:** Solo socios pueden registrar retiros.

### Distribución
**Definición:** Reparto formal de utilidades entre todos los socios del estudio.
**Frecuencia:** Típicamente mensual o cuando se decide.
**En el sistema:** Se registran montos para cada uno de los 5 socios.

### Rentabilidad
**Definición:** Porcentaje que indica cuánto queda de ganancia respecto a los ingresos.
**Fórmula:** ((Ingresos - Gastos) / Ingresos) × 100
**Ejemplo:** Si facturaste $100 y gastaste $30, rentabilidad = 70%
**En el sistema:** Se muestra en el Dashboard como porcentaje.

### Margen Operativo
**Definición:** Sinónimo de rentabilidad operativa.
**Qué indica:** Eficiencia del estudio en generar ganancias.

### Tipo de Cambio (T.C.)
**Definición:** Valor de una moneda expresada en otra.
**En el sistema:** USD a UYU, se obtiene automáticamente del BCU.
**Ejemplo:** Si T.C. = 42.50, entonces USD 1 = $42.50 UYU

### Monto Original
**Definición:** Valor de la operación en la moneda en que se realizó.
**En el sistema:** Se ingresa al registrar y se convierte usando el T.C.

### Monto UYU
**Definición:** Valor de la operación expresado en Pesos Uruguayos.
**Cálculo:** Si la operación fue en USD, se multiplica por T.C.

### Monto USD
**Definición:** Valor de la operación expresado en Dólares.
**Cálculo:** Si la operación fue en UYU, se divide por T.C.

---

## Términos del Negocio

### Área
**Definición:** Departamento o sección del estudio que genera ingresos o gastos.
**Áreas del sistema:**
| Área | Descripción |
|------|-------------|
| Jurídica | Servicios legales, litigios, contratos |
| Notarial | Servicios notariales, escrituras |
| Contable | Servicios contables, impuestos, asesoría |
| Recuperación | Gestión de cobranzas, recupero de deudas |
| Administración | Servicios administrativos generales |
| Otros Gastos | Gastos operativos no atribuibles a un área |

### Localidad
**Definición:** Ubicación física de la oficina.
**Localidades del sistema:**
| Localidad | Descripción |
|-----------|-------------|
| Montevideo (MVD) | Oficina principal |
| Mercedes | Oficina secundaria |

### Cliente
**Definición:** Persona o empresa que paga por los servicios del estudio.
**En ingresos:** Se registra el nombre del cliente que paga.

### Proveedor
**Definición:** Persona o empresa a quien el estudio le paga.
**En gastos:** Se registra el nombre del proveedor.

### Socio
**Definición:** Dueño o copropietario del estudio con acceso completo al sistema.
**Socios del sistema:** Agustina, Viviana, Gonzalo, Pancho, Bruno
**Permisos:** Acceso a todas las funciones, incluido CFO AI y administración.

### Colaborador
**Definición:** Empleado o asistente del estudio con acceso limitado.
**Permisos:** Solo puede registrar ingresos y gastos, sin ver métricas.

---

## Términos del Sistema

### Dashboard
**Definición:** Pantalla principal donde se ven las métricas y accesos rápidos.
**Contenido:** Cards de métricas, gráficos, botones de operaciones.

### Modal
**Definición:** Ventana emergente que aparece sobre el contenido principal.
**Uso:** Para registrar operaciones, cambiar contraseña, etc.

### Sidebar
**Definición:** Menú lateral izquierdo con las opciones de navegación.
**Contenido:** Dashboard, Operaciones, CFO AI, Configuración, etc.

### Header
**Definición:** Barra superior fija con fecha, filtros y usuario.

### Filtros
**Definición:** Controles para limitar qué datos se muestran.
**Tipos:** Por fecha, localidad, moneda.

### Badge
**Definición:** Etiqueta pequeña con información.
**Uso:** Identificar tipo de operación, rol de usuario, etc.

### Toast
**Definición:** Mensaje emergente temporal que confirma una acción.
**Colores:** Verde = éxito, Rojo = error.

### Panel
**Definición:** Sección deslizable desde el lateral.
**Ejemplos:** Panel de Operaciones, Panel de CFO AI.

### Soft Delete
**Definición:** Eliminación lógica (no física) de un registro.
**En el sistema:** Las operaciones "eliminadas" se marcan con fecha/hora, pero no se borran de la base de datos.

---

## Términos Técnicos

### JWT (JSON Web Token)
**Definición:** Token de seguridad que identifica tu sesión.
**En el sistema:** Se genera al loguearte y se envía con cada petición.

### BCU (Banco Central del Uruguay)
**Definición:** Institución que publica el tipo de cambio oficial.
**En el sistema:** Se consulta automáticamente para obtener T.C.

### API
**Definición:** Interfaz de programación de aplicaciones.
**En el sistema:** El frontend se comunica con el backend mediante API.

### UUID
**Definición:** Identificador único universal.
**En el sistema:** Cada operación, usuario, área tiene un UUID único.

---

## Acrónimos

| Acrónimo | Significado |
|----------|-------------|
| UYU | Pesos Uruguayos |
| USD | Dólares Estadounidenses |
| T.C. | Tipo de Cambio |
| MVD | Montevideo |
| BCU | Banco Central del Uruguay |
| CFO | Chief Financial Officer (Director Financiero) |
| AI | Artificial Intelligence (Inteligencia Artificial) |
