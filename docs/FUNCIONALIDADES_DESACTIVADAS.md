# Funcionalidades desactivadas

Última revisión: 15/10/2026.

Estas funcionalidades existen en el código pero están **apagadas en producción**
porque dependen de servicios externos que no están configurados. Mientras
estuvieron "prendidas" sin configurar no funcionaron nunca, y la DGR además
dejaba procesos de navegador colgados en el servidor: eso agotó sus recursos
y tumbó el login el 15/10/2026.

El código **no se borró**: queda apagado con un interruptor. Para prenderlo no
hace falta programar, solo configurar variables en Railway.

## Cómo funcionan los interruptores

Están en `backend/app/core/funcionalidades.py`. Una funcionalidad se prende
solo si se cumplen **las dos** condiciones:

1. Su variable de habilitación está en `true` (decisión explícita).
2. Su credencial está cargada (sin credencial no puede funcionar).

Si falta cualquiera de las dos, queda apagada. Si alguien intenta usarla, el
sistema responde con un mensaje claro (error 503) en vez de fallar o abrir un
navegador. Al arrancar, el servidor anota en el log cuáles están apagadas.

## Qué está apagado

| Funcionalidad | Qué hacía | Por qué está apagada | Para prenderla (variables en Railway) |
|---|---|---|---|
| **Monitoreo automático DGR** | Cada 4 h consultaba en la web de la DGR el estado de los trámites registrales y avisaba cambios. | Necesita resolver el captcha de la DGR con **CapSolver** (servicio pago) y la clave nunca se configuró. Cada intento abría un navegador que no podía consultar nada. | `DGR_HABILITADO=true` + `CAPSOLVER_API_KEY` |
| **Sincronizar un trámite DGR** (botón manual) | Igual que el anterior, a pedido. | Mismo motivo. | Igual que el anterior |
| **Consultas DGI del módulo Contable** (certificado único, IRPF, residencia fiscal, afiliación bancaria, borradores IASS, estado de trámite, expediente administrativo, exoneración de arrendamientos, constancia primaria, devolución IVA gasoil) | Consultaba datos de clientes en la web de la DGI. | Todas resuelven captcha con **CapSolver**. En producción hay **0 consultas registradas**: nunca se usó. | `DGI_CONSULTAS_HABILITADAS=true` + `CAPSOLVER_API_KEY` |
| **Avisos por Telegram** (movimientos de expedientes y cambios DGR) y vinculación de usuarios con Telegram | Mandaba avisos al bot `@Cfo_inteligente_bot`. | El token del bot no está configurado y ningún usuario tiene Telegram vinculado. | `TELEGRAM_HABILITADO=true` + `TELEGRAM_BOT_TOKEN` |

## Qué sigue funcionando

- **Registro de trámites DGR**: se pueden cargar, listar y borrar. Se guardan
  sin los datos de la DGR (eso lo traía la consulta automática).
- **Sincronización de expedientes con el Poder Judicial** (7:30 todos los
  días): funciona; solo se omite el aviso por Telegram.
- **Historial de consultas Contable**: se puede ver; lo que no se puede es
  hacer consultas nuevas.
- Todo lo demás del sistema (operaciones, dashboard, ALA, contratos, casos,
  indicadores, soporte, mail diario de actividad).

## Antes de prender algo

- **DGR o DGI**: además de la clave de CapSolver, revisar el costo por
  captcha. Prender primero en un horario de poco uso y mirar los logs de
  Railway del día siguiente: no debería aparecer `can't start new thread`.
- **Telegram**: cada usuario tiene que vincular su chat con el bot.
