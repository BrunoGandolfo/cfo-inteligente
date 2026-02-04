# Módulo ALA - Anti-Lavado de Activos

## Resumen rápido
El módulo ALA (Anti-Lavado de Activos) permite verificar personas contra listas internacionales de sanciones y personas políticamente expuestas (PEP) para cumplir con la normativa uruguaya de prevención de lavado de activos y financiamiento del terrorismo.

## ¿Qué es ALA?

ALA es el módulo de Anti-Lavado de Activos del sistema. Permite verificar personas contra múltiples bases de datos internacionales para identificar posibles riesgos relacionados con:
- Personas políticamente expuestas (PEP)
- Listas de sanciones internacionales
- Personas vinculadas con actividades ilícitas
- Cumplimiento normativo (Decreto 379/018, SENACLAFT)

## ¿Para qué sirve?

El módulo ALA es esencial para:
- Cumplir con la normativa uruguaya de prevención de lavado de activos
- Verificar clientes antes de realizar operaciones importantes
- Identificar personas políticamente expuestas (PEP)
- Detectar posibles riesgos en transacciones
- Generar certificados de verificación con validez legal
- Mantener un registro de verificaciones realizadas

## Contexto legal

El módulo cumple con:
- **Decreto 379/018**: Normativa uruguaya sobre prevención de lavado de activos
- **SENACLAFT**: Servicio de Prevención y Lucha contra el Lavado de Activos y Financiamiento del Terrorismo
- **Normativa internacional**: Estándares del GAFI (Grupo de Acción Financiera Internacional)

Es una herramienta de cumplimiento normativo que ayuda a las empresas a cumplir con sus obligaciones legales.

## Listas que se consultan

El sistema verifica contra las siguientes bases de datos:

### 1. PEP Uruguay (5,737 registros)
Lista oficial de Personas Políticamente Expuestas de Uruguay. Incluye:
- Funcionarios públicos actuales y anteriores
- Familiares directos de funcionarios
- Personas cercanas a funcionarios públicos

### 2. ONU (726 registros)
Lista de sanciones de las Naciones Unidas. Incluye:
- Personas y entidades sancionadas por el Consejo de Seguridad
- Organizaciones terroristas
- Regímenes sancionados

### 3. OFAC (18,598 registros)
Oficina de Control de Activos Extranjeros de Estados Unidos. Incluye:
- Personas y entidades sancionadas por EE.UU.
- Listas de sanciones económicas
- Personas vinculadas con actividades ilícitas

### 4. UE (23,471 registros)
Lista de sanciones de la Unión Europea. Incluye:
- Personas y entidades sancionadas por la UE
- Restricciones financieras
- Medidas restrictivas

**Total**: Más de 48,000 registros verificados automáticamente.

## Cómo hacer una verificación

### Paso a paso:

1. **Accedé al módulo ALA**
   - Desde el menú lateral, hacé clic en "ALA"
   - Se abre la página de verificaciones

2. **Hacé clic en "Nueva Verificación"**
   - Botón en la parte superior
   - Se abre un formulario

3. **Completá los datos de la persona**
   - **Nombre completo**: Nombre y apellidos de la persona a verificar
   - **Cédula de Identidad**: Número de CI (si es uruguayo/a)
   - **Fecha de nacimiento**: Fecha de nacimiento (opcional pero recomendado)
   - **Nacionalidad**: Nacionalidad de la persona

4. **Seleccioná el tipo de operación**
   - Tipo de transacción o operación que estás realizando
   - Ejemplos: Compraventa de inmueble, apertura de cuenta, etc.

5. **Ingresá el monto** (si aplica)
   - Monto en USD de la operación
   - Ayuda a determinar el nivel de riesgo

6. **Ejecutá la verificación**
   - Hacé clic en "Verificar"
   - El sistema consulta todas las listas automáticamente
   - El proceso puede demorar unos segundos

7. **Revisá los resultados**
   - El sistema muestra si hay coincidencias
   - Podés ver los detalles de cada coincidencia encontrada

## Interpretación de resultados

### Coincidencia exacta
- El nombre y datos coinciden exactamente con un registro en alguna lista
- **Acción**: Revisar cuidadosamente los detalles
- Puede requerir medidas adicionales de verificación

### Coincidencia parcial
- Hay similitudes pero no coincidencia exacta
- **Acción**: Revisar los detalles para confirmar si es la misma persona
- Puede ser un falso positivo (personas con nombres similares)

### Sin coincidencia
- No se encontraron coincidencias en ninguna lista
- **Acción**: Puedes proceder con la operación normalmente
- Se recomienda guardar el certificado de verificación

## Clasificación de riesgo

El sistema clasifica el riesgo según varios factores:

- **Alto riesgo**: Coincidencias en listas de sanciones o PEP de alto nivel
- **Medio riesgo**: Coincidencias parciales o PEP de nivel medio
- **Bajo riesgo**: Sin coincidencias o PEP de bajo nivel

La clasificación ayuda a determinar qué medidas adicionales pueden ser necesarias.

## Búsquedas complementarias Art. 44 C.4

El sistema realiza búsquedas complementarias según el Artículo 44, literal C.4 de la normativa:

### ¿Qué son?
Búsquedas adicionales en fuentes públicas para obtener más información sobre la persona verificada.

### ¿Cómo funcionan?
1. El sistema busca información en Wikipedia
2. Utiliza inteligencia artificial para analizar los resultados
3. Genera un resumen de información pública disponible
4. Identifica posibles vínculos o información relevante

### ¿Para qué sirven?
- Obtener contexto adicional sobre la persona
- Identificar posibles vínculos no evidentes
- Completar el perfil de riesgo
- Cumplir con requisitos normativos adicionales

Los resultados de las búsquedas complementarias se incluyen en el certificado de verificación.

## Certificado PDF

Después de cada verificación, podés generar un certificado PDF con validez legal.

### ¿Qué incluye el certificado?
- Datos de la persona verificada
- Resultados de la verificación en cada lista
- Fecha y hora de la verificación
- Clasificación de riesgo
- Resultados de búsquedas complementarias
- Hash de integridad (SHA-256) para verificar que no fue modificado

### ¿Para qué sirve el hash?
El hash de integridad permite verificar que el certificado no ha sido alterado después de su generación. Es una medida de seguridad que garantiza la autenticidad del documento.

### Cómo generarlo:
1. Después de una verificación, hacé clic en "Generar Certificado PDF"
2. El sistema genera el PDF con toda la información
3. Podés descargarlo y guardarlo para tus registros
4. El certificado tiene validez legal para cumplimiento normativo

## Ver verificaciones anteriores

Podés ver todas las verificaciones que realizaste:

1. En la página principal de ALA, se muestra una lista de verificaciones
2. Cada verificación muestra:
   - Nombre de la persona verificada
   - Fecha de verificación
   - Resultado (coincidencia encontrada o sin coincidencias)
   - Clasificación de riesgo
3. Hacé clic en una verificación para ver los detalles completos
4. Podés generar el certificado PDF en cualquier momento

## Información técnica

### Fuentes de datos:
- **PEP Uruguay**: Catálogo de Datos Abiertos del gobierno uruguayo
- **ONU**: Servicio web oficial de sanciones de las Naciones Unidas
- **OFAC**: Base de datos oficial de la Oficina de Control de Activos Extranjeros
- **UE**: Base de datos oficial de sanciones de la Unión Europea

### Actualización de listas:
Las listas se actualizan automáticamente desde las fuentes oficiales para garantizar que siempre tengas la información más reciente.

### Seguridad:
Todas las verificaciones se registran con fecha, hora y usuario que las realizó. Los certificados incluyen hash de integridad para prevenir modificaciones.

## Preguntas frecuentes

### ¿Cuánto tiempo demora una verificación?
Una verificación completa puede demorar entre 5 y 15 segundos, dependiendo de la cantidad de listas que se consulten y si se realizan búsquedas complementarias.

### ¿Qué hago si encuentro una coincidencia?
Si encontrás una coincidencia, revisá cuidadosamente los detalles para confirmar si es la misma persona. En caso de duda, consultá con el área de cumplimiento o con un supervisor antes de proceder con la operación.

### ¿Puedo verificar varias personas a la vez?
Actualmente, cada verificación se realiza de forma individual. Si necesitás verificar múltiples personas, realizá verificaciones separadas para cada una.

### ¿El certificado tiene validez legal?
Sí, el certificado PDF generado tiene validez legal para cumplimiento normativo. Incluye hash de integridad que garantiza que no ha sido modificado.

### ¿Qué pasa si no tengo todos los datos de la persona?
Podés realizar la verificación con los datos que tengas disponibles. Sin embargo, cuantos más datos proporciones (especialmente CI y fecha de nacimiento), más precisa será la verificación y menor la posibilidad de falsos positivos.

### ¿Se guardan los datos de las personas verificadas?
Sí, las verificaciones se guardan en el sistema con fines de cumplimiento normativo y auditoría. Los datos se manejan con estricta confidencialidad según la normativa de protección de datos.
